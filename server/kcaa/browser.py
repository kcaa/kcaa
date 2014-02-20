#!/usr/bin/env python

import logging
import time
import traceback

from selenium import webdriver
from selenium.webdriver.common import action_chains


KANCOLLE_URL = 'http://www.dmm.com/netgame/social/-/gadgets/=/app_id=854854/'


def get_desired_capabilities(args):
    capabilities = {}
    capabilities['proxy'] = {'httpProxy': args.proxy,
                             'ftpProxy': args.proxy,
                             'sslProxy': args.proxy,
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


def get_game_frame(browser, game_frame):
    if game_frame:
        return game_frame
    try:
        game_frame = browser.find_element_by_id('game_frame')
        game_frame.click()
        # TODO: Possibly there's a better way to center the game frame.
        browser.execute_script('window.scrollBy(0, -50);')
        return game_frame
    except:
        return None


def setup_kancolle_browser(args, to_exit):
    try:
        monitor = BrowserMonitor('Kancolle', open_kancolle_browser(args), 5)
        game_frame = None
        while True:
            browser = monitor.browser
            time.sleep(1.0)
            if to_exit.wait(0.0):
                break
            if not monitor.is_alive():
                # If a user closes the Kancolle browser, it should be a signal
                # that the user wants to exit the game.
                break
            game_frame = get_game_frame(browser, game_frame)
            if game_frame:
                while server_conn.poll():
                    request = server_conn.recv()
                    event_type = request[0]
                    if event_type == 'click':
                        x, y = request[1:]
                        actions = action_chains.ActionChains(browser)
                        actions.move_to_element_with_offset(game_frame, x, y)
                        actions.click(None)
                        actions.perform()
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
