#!/usr/bin/env python

import logging
import os.path
import time
import traceback

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common import action_chains


KANCOLLE_URL = 'http://www.dmm.com/netgame/social/-/gadgets/=/app_id=854854/'

COMMAND_CLICK = 'click'
COMMAND_COVER = 'cover'
COMMAND_TAKE_SCREENSHOT = 'take_screenshot'


logger = logging.getLogger('kcaa.browser')


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


def setup_phantomjs(args, desired_capabilities):
    return webdriver.PhantomJS(args.phantomjs_binary,
                               desired_capabilities=desired_capabilities)


def open_browser(browser_type, args):
    desired_capabilities = get_desired_capabilities(args)
    browser = None
    if browser_type == 'chrome':
        browser = setup_chrome(args, desired_capabilities)
    elif browser_type == 'firefox':
        browser = setup_firefox(args, desired_capabilities)
    elif browser_type == 'phantomjs':
        browser = setup_phantomjs(args, desired_capabilities)
    else:
        raise ValueError('Unrecognized browser: {browser}'.format(
            browser=browser_type))
    return browser


def open_kancolle_browser(args):
    browser = open_browser(args.kancolle_browser, args)
    browser.set_window_size(980, 780)
    browser.set_window_position(0, 0)
    browser.get(KANCOLLE_URL)
    if args.credentials and os.path.isfile(args.credentials):
        with open(args.credentials, 'r') as credentials_file:
            user, passwd = credentials_file.read().strip().split(':')
            login_id = browser.find_element_by_id('login_id')
            login_id.send_keys(user)
            password = browser.find_element_by_id('password')
            password.send_keys(passwd)
            browser.get_screenshot_as_file('screen.png')
            last_exception = None
            for _ in xrange(5):
                try:
                    login_button = browser.find_element_by_xpath(
                        '//div[@class="box-btn-login"]//input[@type="submit"]')
                    login_button.click()
                    break
                except exceptions.NoSuchElementException:
                    logger.info('The page must have transitioned. Continuing.')
                    break
                except exceptions.WebDriverException as e:
                    last_exception = e
                    logger.warning(
                        'Seems like page loading failed. This may be just a '
                        'transient error, so retrying.')
                    time.sleep(1.0)
            else:
                browser.get_screenshot_as_file('screen.png')
                logger.fatal(
                    'Login failed. Check the generated screenshot '
                    '(screen.png) to see if there is any visible error.')
                raise last_exception
    return browser


def get_game_frame(browser):
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
    add_game_frame_cover(browser, game_area_width, game_area_height, dx, dy)
    # If in the debug mode, show the digitizer tools.
    add_digitizer(browser)
    return game_frame, dx, dy


def add_game_frame_cover(browser, game_area_width, game_area_height, dx, dy):
    browser.execute_script('''
        var gameFrame = document.querySelector("#game_frame");
        var frameRect = gameFrame.getBoundingClientRect();
        var gameFrameCover = document.createElement("div");
        gameFrameCover.id = "game_frame_cover";
        gameFrameCover.style.boxShadow =
            "0 0 50px 50px hsla(240, 80%, 20%, 0.5) inset";
        gameFrameCover.style.boxSizing = "border-box";
        gameFrameCover.style.color = "white";
        gameFrameCover.style.display = "none";
        gameFrameCover.style.fontSize = "30px";
        gameFrameCover.style.height = ''' + str(game_area_height) + ''' + "px";
        gameFrameCover.style.left =
            Math.floor(frameRect.left + ''' + str(dx) + ''') + "px";
        gameFrameCover.style.padding = "20px";
        gameFrameCover.style.position = "absolute";
        gameFrameCover.style.textAlign = "right";
        gameFrameCover.style.textShadow = "0 0 5px black";
        gameFrameCover.style.top =
            Math.floor(frameRect.top + ''' + str(dy) + ''') + "px";
        gameFrameCover.style.width = ''' + str(game_area_width) + ''' + "px";
        gameFrameCover.style.zIndex = "1";
        gameFrameCover.textContent = "Being automatically manipulated";
        document.body.appendChild(gameFrameCover);
    ''')


def add_digitizer(browser):
    browser.execute_script('''
        var gameFrameCover = document.querySelector("#game_frame_cover");

        var digitizerDisplay = document.createElement("div");
        digitizerDisplay.style.fontSize = "16px";
        digitizerDisplay.style.position = "absolute";
        var toggleButton = document.createElement("button");
        toggleButton.textContent = "Toggle Cover";
        toggleButton.onclick = function (e) {
            var isCurrentlyShown = gameFrameCover.style.display != "none";
            gameFrameCover.style.display = isCurrentlyShown ? "none" : "block";
        }
        digitizerDisplay.appendChild(toggleButton);
        var coordinates = document.createElement("span");
        coordinates.style.marginLeft = "10px";
        digitizerDisplay.appendChild(coordinates);
        var w = document.querySelector("#w");
        w.insertBefore(digitizerDisplay, w.children[0]);

        gameFrameCover.onmousemove = function (e) {
            var frameRect = gameFrameCover.getBoundingClientRect();
            var x = e.clientX - frameRect.left;
            var y = e.clientY - frameRect.top;
            coordinates.textContent = "(" + x + "," + y + ")";
        }
    ''')


def show_game_frame_cover(browser, is_shown):
    display = 'block' if is_shown else 'none'
    browser.execute_script('''
        var gameFrameCover = document.querySelector("#game_frame_cover");
        gameFrameCover.style.display = "''' + display + '''";
    ''')


def setup_kancolle_browser(args, controller_conn, to_exit):
    try:
        monitor = BrowserMonitor('Kancolle', open_kancolle_browser(args), 5)
        game_frame, dx, dy = None, None, None
        while True:
            browser = monitor.browser
            if to_exit.wait(0.0):
                break
            if not monitor.is_alive():
                # If a user closes the Kancolle browser, it should be a signal
                # that the user wants to exit the game.
                break
            if game_frame:
                while controller_conn.poll(1.0):
                    command_type, command_args = controller_conn.recv()
                    if command_type == COMMAND_CLICK:
                        x, y = command_args
                        x += dx
                        y += dy
                        actions = action_chains.ActionChains(browser)
                        actions.move_to_element_with_offset(game_frame, x, y)
                        actions.click(None)
                        show_game_frame_cover(browser, False)
                        actions.perform()
                        show_game_frame_cover(browser, True)
                    elif command_type == COMMAND_COVER:
                        is_shown = command_args[0]
                        show_game_frame_cover(browser, is_shown)
                    elif command_type == COMMAND_TAKE_SCREENSHOT:
                        controller_conn.send(
                            browser.get_screenshot_as_png())
                    else:
                        raise ValueError(
                            'Unknown browser command: type = {}, args = {}'
                            .format(command_type, command_args))
            else:
                game_frame, dx, dy = get_game_frame(browser)
                time.sleep(1.0)
    except:
        traceback.print_exc()
    to_exit.set()
    try:
        monitor.close()
    except:
        pass


def open_kcaa_browser(args, root_url):
    if not args.kcaa_browser:
        logger.info('Flag --kcaa_browser is set to be empty. Do not start up '
                    'one for KCAA. You can still open a KCAA Web UI with {}.'
                    .format(root_url))
        return None
    browser = open_browser(args.kcaa_browser, args)
    browser.set_window_size(700, 1050)
    browser.set_window_position(980, 0)
    browser.get(root_url)
    return browser


def setup_kcaa_browser(args, root_url, to_exit):
    try:
        kcaa_browser = open_kcaa_browser(args, root_url)
        if not kcaa_browser:
            return
        monitor = BrowserMonitor('KCAA', kcaa_browser, 5)
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
            logger.debug('Browser {} not responding.'.format(self.name))
            self.credit -= 1
            alive = False
        if alive and self.credit < self.max_credit:
            logger.info('Browser recovered.')
            self.credit = self.max_credit
        return self.credit > 0
