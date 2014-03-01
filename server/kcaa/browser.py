#!/usr/bin/env python

import Queue
import logging
import time
import traceback

from selenium import webdriver
from selenium.webdriver.common import action_chains


KANCOLLE_URL = 'http://www.dmm.com/netgame/social/-/gadgets/=/app_id=854854/'

COMMAND_CLICK = 'click'


def get_desired_capabilities(args):
    capabilities = {}
    capabilities['proxy'] = {'httpProxy': args.proxy,
                             'ftpProxy': args.proxy,
                             'sslProxy': None,
                             'noProxy': '127.0.0.1,localhost',
                             'proxyType': 'MANUAL',
                             'class': 'org.openqa.selenium.Proxy',
                             'autodetect': False}
    return capabilities


def setup_chrome(args, desired_capabilities):
    options = webdriver.ChromeOptions()
    options.binary_location = args.chrome_binary
    return webdriver.Chrome(executable_path=args.chromedriver_binary,
                            chrome_options=options,
                            desired_capabilities=desired_capabilities)


def setup_firefox(args, desired_capabilities):
    return webdriver.Firefox(capabilities=desired_capabilities)


def open_browser(args):
    desired_capabilities = get_desired_capabilities(args)
    browser = None
    if args.browser == 'chrome':
        browser = setup_chrome(args, desired_capabilities)
    elif args.browser == 'firefox':
        browser = setup_firefox(args, desired_capabilities)
    else:
        raise ValueError('Unrecognized browser: {browser}'.format(
            browser=args.browser))
    return browser


def open_kancolle_browser(args):
    browser = open_browser(args)
    browser.set_window_size(980, 780)
    browser.set_window_position(0, 0)
    browser.get(KANCOLLE_URL)
    if args.credentials:
        with open(args.credentials, 'r') as credentials_file:
            user, passwd = credentials_file.read().strip().split(':')
            login_id = browser.find_element_by_id('login_id')
            login_id.send_keys(user)
            password = browser.find_element_by_id('password')
            password.send_keys(passwd)
            login_button = browser.find_element_by_xpath(
                '//div[@class="box-btn-login"]//input[@type="submit"]')
            login_button.click()
    return browser


def get_game_frame(browser, game_frame, dx, dy):
    if game_frame:
        return game_frame, dx, dy
    # Is there a better way to get this? Currently these are read from the
    # iframe source.
    game_area_width = 800
    game_area_height = 480
    game_area_top = 16
    try:
        game_frame = browser.find_element_by_id('game_frame')
    except:
        return None, None, None
    dx = (game_frame.size['width'] - game_area_width) / 2
    dy = game_area_top
    add_digitizer(browser, game_area_width, game_area_height, dx, dy)
    return game_frame, dx, dy


def add_digitizer(browser, game_area_width, game_area_height, dx, dy):
    browser.execute_script('''
        var game_frame = document.getElementById("game_frame");
        var frameRect = game_frame.getBoundingClientRect();
        var digitizer = document.createElement("div");
        digitizer.style.backgroundColor = "hsla(0, 50%, 50%, 0.5)";
        digitizer.style.display = "none";
        digitizer.style.height = ''' + str(game_area_height) + ''' + "px";
        digitizer.style.left =
            Math.floor(frameRect.left + ''' + str(dx) + ''') + "px";
        digitizer.style.position = "absolute";
        digitizer.style.top =
            Math.floor(frameRect.top + ''' + str(dy) + ''') + "px";
        digitizer.style.width = ''' + str(game_area_width) + '''+ "px";
        digitizer.style.zIndex = "1";
        digitizer.onmousemove = function (e) {
            var rect = digitizer.getBoundingClientRect();
            window.location.hash = (e.clientX - rect.left) + "," +
                (e.clientY - rect.top);
        }
        digitizer.onclick = function (e) {
            digitizer.style.display = "none";
        }
        document.body.appendChild(digitizer);
        var show_digitizer = document.createElement("button");
        show_digitizer.textContent = "Show Digitizer";
        show_digitizer.style.position = "absolute";
        show_digitizer.onclick = function (e) {
            digitizer.style.display = "block";
        }
        var w = document.getElementById("w");
        w.insertBefore(show_digitizer, w.children[0]);
    ''')


def setup_kancolle_browser(args, click_queue, to_exit):
    try:
        monitor = BrowserMonitor('Kancolle', open_kancolle_browser(args), 5)
        game_frame, dx, dy = None, None, None
        while True:
            browser = monitor.browser
            time.sleep(1.0)
            if to_exit.wait(0.0):
                break
            if not monitor.is_alive():
                # If a user closes the Kancolle browser, it should be a signal
                # that the user wants to exit the game.
                break
            game_frame, dx, dy = get_game_frame(browser, game_frame, dx, dy)
            if game_frame:
                try:
                    while True:
                        x, y = click_queue.get_nowait()
                        x += dx
                        y += dy
                        actions = action_chains.ActionChains(browser)
                        actions.move_to_element_with_offset(game_frame, x, y)
                        actions.click(None)
                        actions.perform()
                except Queue.Empty:
                    pass
    except:
        traceback.print_exc()
    to_exit.set()
    try:
        monitor.close()
    except:
        pass


def open_kcaa_browser(args, root_url):
    browser = open_browser(args)
    browser.set_window_size(700, 1050)
    browser.set_window_position(980, 0)
    browser.get(root_url)
    return browser


def setup_kcaa_browser(args, root_url, to_exit):
    try:
        monitor = BrowserMonitor('KCAA', open_kcaa_browser(args, root_url), 5)
        while True:
            time.sleep(1.0)
            if to_exit.wait(0.0):
                break
            if not monitor.is_alive():
                # KCAA window is not vital for playing the game -- it is not
                # necessarily a signal for exiting. Rather, I would restart it
                # again, assuming that was an accident.
                monitor = BrowserMonitor(
                    'KCAA', open_kcaa_browser(args, root_url), 5)
    except:
        traceback.print_exc()
    to_exit.set()
    try:
        monitor.close()
    except:
        pass


class BrowserMonitor(object):

    def __init__(self, name, browser, max_credit):
        self._logger = logging.getLogger('kcaa.browser')
        self.name = name
        self.browser = browser
        self.max_credit = max_credit
        self.credit = max_credit

    def close(self):
        try:
            self.browser.close()
        except Exception:
            pass

    def is_alive(self):
        alive = True
        try:
            # Check window_handles as a heartbeat.
            # This seems better than current_url or title because they
            # interfere with Chrome developer tools.
            if self.browser.window_handles is None:
                # This won't occur (as an exception will be thrown instead)
                # but to make sure the above condition is evaluated.
                raise RuntimeError()
        except Exception:
            # Browser exited, or didn't respond.
            self._logger.debug('Browser {} not responding.'.format(self.name))
            self.credit -= 1
            alive = False
        if alive and self.credit < self.max_credit:
            self._logger.info('Browser recovered.')
            self.credit = self.max_credit
        return self.credit > 0
