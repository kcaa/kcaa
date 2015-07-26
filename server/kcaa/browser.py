#!/usr/bin/env python

import cStringIO
import logging
import os.path
import time
import traceback

from PIL import Image
from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common import action_chains

import logenv


KANCOLLE_URL = 'http://www.dmm.com/netgame/social/-/gadgets/=/app_id=854854/'

COMMAND_CLICK = 'click'
COMMAND_CLICK_HOLD = 'click_hold'
COMMAND_CLICK_RELEASE = 'click_release'
COMMAND_MOVE_MOUSE = 'move_mouse'
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


def setup_chrome(name, args, desired_capabilities, is_chromium):
    options = webdriver.ChromeOptions()
    options.binary_location = (
        args.chromium_binary if is_chromium else args.chrome_binary)
    if args.chrome_user_data_basedir:
        options.add_argument('--user-data-dir={}'.format(
            os.path.join(args.chrome_user_data_basedir, name)))
    # Do not ignore SSL certificate errors.
    # See also other Chrome-specific capabilities at
    # https://sites.google.com/a/chromium.org/chromedriver/capabilities
    options.add_experimental_option('excludeSwitches', [
        'ignore-certificate-errors'])
    return webdriver.Chrome(executable_path=args.chromedriver_binary,
                            chrome_options=options,
                            desired_capabilities=desired_capabilities)


def setup_firefox(name, args, desired_capabilities):
    return webdriver.Firefox(capabilities=desired_capabilities)


def setup_phantomjs(name, args, desired_capabilities):
    # Use PhantomJS with caution: it doesn't support proxying only HTTP
    # transactions (= bypassing HTTPS ones). This may reveal your username and
    # password to anyone who can access the proxy server, or anyone who can run
    # a malicious process on the machine where KCAA runs.
    # TODO: Support 'https' in --proxy-type in PhantomJS, and make it
    # distinguishable from 'http'
    service_args = [
        '--proxy={}'.format(args.proxy),
        '--proxy-type=http',
        '--ignore-ssl-errors=true',
    ]
    browser = webdriver.PhantomJS(args.phantomjs_binary,
                                  service_args=service_args,
                                  desired_capabilities=desired_capabilities)
    return browser


def open_browser(name, browser_type, args):
    desired_capabilities = get_desired_capabilities(args)
    browser = None
    if browser_type == 'chrome':
        browser = setup_chrome(name, args, desired_capabilities, False)
    elif browser_type == 'chromium':
        browser = setup_chrome(name, args, desired_capabilities, True)
    elif browser_type == 'firefox':
        browser = setup_firefox(name, args, desired_capabilities)
    elif browser_type == 'phantomjs':
        browser = setup_phantomjs(name, args, desired_capabilities)
    else:
        raise ValueError('Unrecognized browser: {browser}'.format(
            browser=browser_type))
    return browser


def open_kancolle_browser(args):
    logger.info('Opening Kancolle browser...')
    browser = open_browser('kancolle', args.kancolle_browser, args)
    browser.set_window_size(980, 750)
    browser.set_window_position(0, 0)
    logger.info('Opening the Kancolle game URL...')
    browser.get(KANCOLLE_URL)
    if args.credentials and os.path.isfile(args.credentials):
        logger.info('Trying to sign in with the given credentials...')
        with open(args.credentials, 'r') as credentials_file:
            user, passwd = credentials_file.read().strip().split(':')
            try:
                login_id = browser.find_element_by_id('login_id')
                login_id.send_keys(user)
                password = browser.find_element_by_id('password')
                password.send_keys(passwd)
                last_exception = None
                for _ in xrange(5):
                    logger.info('Login trial...')
                    time.sleep(1.0)
                    try:
                        login_button = browser.find_element_by_xpath(
                            '//div[@class="box-btn-login"]'
                            '//input[@type="submit"]')
                        login_button.click()
                        break
                    except exceptions.NoSuchElementException:
                        logger.info('The page must have transitioned..')
                        break
                    except exceptions.WebDriverException as e:
                        last_exception = e
                        logger.info(
                            'Seems like page loading failed. This may be just'
                            'a transient error in a browser like phantomjs. '
                            'Retrying.')
                else:
                    raise last_exception
            except Exception as e:
                browser.get_screenshot_as_file('screen.png')
                logger.error(str(e))
                logger.fatal(
                    'Login failed. Check the generated screenshot '
                    '(screen.png) to see if there is any visible error.')
                raise e
    logger.info('Kancolle browser is ready.')
    return browser


def get_game_frame(browser, debug):
    # Is there a better way to get this? Currently these are read from the
    # iframe source.
    game_area_width = 800
    game_area_height = 480
    game_area_top = 16
    try:
        game_frame = browser.find_element_by_id('game_frame')
    except:
        return None, None, None, None
    dx = (game_frame.size['width'] - game_area_width) / 2
    dy = game_area_top
    add_game_frame_cover(browser, game_area_width, game_area_height, dx, dy)
    # If in the debug mode, show the digitizer tools.
    if debug:
        add_digitizer(browser)
    location = game_frame.location
    left = int(location['x'] + dx)
    top = int(location['y'] + dy)
    return game_frame, dx, dy, (left, top, left + game_area_width,
                                top + game_area_height)


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
        document.body.appendChild(gameFrameCover);
        coverText = document.createElement("span");
        coverText.style.position = "relative";
        coverText.style.top = "410px";
        coverText.textContent = "Automatically manipulated";
        gameFrameCover.appendChild(coverText);
    ''')


def add_digitizer(browser):
    browser.execute_script('''
        var gameFrameCover = document.querySelector("#game_frame_cover");

        var digitizerDisplay = document.createElement("div");
        digitizerDisplay.style.fontSize = "16px";
        digitizerDisplay.style.position = "absolute";
        digitizerDisplay.style.top = "42px";
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
    try:
        # Currently this doesn't work for some long-running environment.
        # It often dies with NoSichWindowExction.
        return True
        browser.execute_script('''
            var gameFrameCover = document.querySelector("#game_frame_cover");
            gameFrameCover.style.display = "''' + display + '''";
        ''')
        return True
    except exceptions.UnexpectedAlertPresentException as e:
        logger.error('Unexpected alert: {}'.format(e.alert_text))
        logger.debug(str(e))
    return False


def perform_actions(actions):
    try:
        actions.perform()
        return True
    except exceptions.UnexpectedAlertPresentException as e:
        logger.error('Unexpected alert: {}'.format(e.alert_text))
        logger.debug(str(e))
    return False


def setup_kancolle_browser(args, controller_conn, to_exit, browser_broken):
    try:
        logenv.setup_logger(args.debug, args.log_file, args.log_level,
                            args.keep_timestamped_logs)
        monitor = BrowserMonitor(
            'Kancolle', open_kancolle_browser(args), 3)
        game_frame, dx, dy, game_area_rect = None, None, None, None
        covered = False
        while True:
            browser = monitor.browser
            if to_exit.wait(0.0):
                logger.info('Browser Kancolle got an exit signal. Shutting '
                            'down.')
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
                        if covered:
                            show_game_frame_cover(browser, False)
                            time.sleep(0.1)
                        perform_actions(actions)
                        if covered:
                            time.sleep(0.1)
                            show_game_frame_cover(browser, True)
                    elif command_type == COMMAND_CLICK_HOLD:
                        logger.debug('click hold!')
                        x, y = command_args
                        x += dx
                        y += dy
                        actions = action_chains.ActionChains(browser)
                        actions.move_to_element_with_offset(game_frame, x, y)
                        actions.click_and_hold(None)
                        if covered:
                            show_game_frame_cover(browser, False)
                            time.sleep(0.1)
                        perform_actions(actions)
                    elif command_type == COMMAND_CLICK_RELEASE:
                        logger.debug('click release!')
                        x, y = command_args
                        x += dx
                        y += dy
                        actions = action_chains.ActionChains(browser)
                        actions.move_to_element_with_offset(game_frame, x, y)
                        actions.release(None)
                        perform_actions(actions)
                        if covered:
                            time.sleep(0.1)
                            show_game_frame_cover(browser, True)
                    elif command_type == COMMAND_MOVE_MOUSE:
                        logger.debug('mouse move!')
                        x, y = command_args
                        x += dx
                        y += dy
                        actions = action_chains.ActionChains(browser)
                        actions.move_to_element_with_offset(game_frame, x, y)
                        perform_actions(actions)
                    elif command_type == COMMAND_COVER:
                        is_shown = command_args[0]
                        if is_shown != covered:
                            show_game_frame_cover(browser, is_shown)
                            covered = is_shown
                    elif command_type == COMMAND_TAKE_SCREENSHOT:
                        format, quality, width, height = command_args
                        im_buffer = None
                        response = ''
                        try:
                            im_buffer = cStringIO.StringIO(
                                browser.get_screenshot_as_png())
                            im = Image.open(im_buffer)
                            im.load()
                            im_buffer.close()
                            im = im.crop(game_area_rect)
                            if width != 0 and height != 0:
                                im.thumbnail((width, height), Image.NEAREST)
                            im_buffer = cStringIO.StringIO()
                            if format == 'jpeg':
                                im.save(im_buffer, format, quality=quality)
                            else:
                                im.save(im_buffer, format)
                            response = im_buffer.getvalue()
                        except exceptions.UnexpectedAlertPresentException as e:
                            logger.error('Unexpected alert: {}'.format(
                                e.alert_text))
                            logger.debug(str(e))
                        finally:
                            controller_conn.send(response)
                            if im_buffer:
                                im_buffer.close()
                    else:
                        raise ValueError(
                            'Unknown browser command: type = {}, args = {}'
                            .format(command_type, command_args))
            else:
                game_frame, dx, dy, game_area_rect = get_game_frame(
                    browser, args.debug)
                time.sleep(1.0)
    except (KeyboardInterrupt, SystemExit):
        logger.info('SIGINT received in the Kancolle browser process. '
                    'Exiting...')
    except exceptions.NoSuchWindowException:
        logger.error('Kancolle window seems to have been killed.')
        browser_broken.set()
        monitor.close()
        return
    except:
        logger.error(traceback.format_exc())
    to_exit.set()
    monitor.close()


def open_kcaa_browser(args, root_url):
    if not args.kcaa_browser:
        logger.info('Flag --kcaa_browser is set to be empty. No browser will '
                    'be up locally. You can still open a KCAA Web UI with {}.'
                    .format(root_url))
        return None
    logger.info('Opening a KCAA browser.')
    browser = open_browser('kcaa', args.kcaa_browser, args)
    browser.set_window_size(700, 1050)
    browser.set_window_position(980, 0)
    logger.info('Opening the KCAA Web UI...')
    browser.get(root_url)
    logger.info('KCAA browser is ready.')
    return browser


def setup_kcaa_browser(args, root_url, to_exit):
    try:
        logenv.setup_logger(args.debug, args.log_file, args.log_level,
                            args.keep_timestamped_logs)
        kcaa_browser = open_kcaa_browser(args, root_url)
        if not kcaa_browser:
            return
        monitor = BrowserMonitor('KCAA', kcaa_browser, 3)
        while True:
            time.sleep(1.0)
            if to_exit.wait(0.0):
                logger.info('Browser KCAA got an exit signal. Shutting down.')
                break
            if not monitor.is_alive():
                # KCAA window is not vital for playing the game -- it is not
                # necessarily a signal for exiting. Rather, I would restart it
                # again, assuming that was an accident.
                monitor = BrowserMonitor(
                    'KCAA', open_kcaa_browser(args, root_url), 3)
    except (KeyboardInterrupt, SystemExit):
        logger.info('SIGINT received in the KCAA browser process. Exiting...')
    except:
        logger.error(traceback.format_exc())
    to_exit.set()
    monitor.close()


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
