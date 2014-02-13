#!/usr/bin/env python

import logging

from selenium import webdriver


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
    browser.set_window_size(980, 800)
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


def open_kcaa_browser(args, url):
    browser = open_browser(args)
    browser.set_window_size(700, 800)
    browser.set_window_position(980, 0)
    browser.get(url)
    return browser


def setup(args, url):
    browsers = [open_kancolle_browser(args), open_kcaa_browser(args, url)]
    return BrowserMonitor(browsers, 5)


class BrowserMonitor(object):

    def __init__(self, browsers, max_credit):
        self._logger = logging.getLogger('kcaa.browser')
        self.browsers = browsers
        self.max_credit = max_credit
        self.credit = max_credit

    def close(self):
        for browser in self.browsers:
            try:
                browser.close()
            except Exception:
                pass

    def is_alive(self):
        alive = True
        try:
            # Check window_handles as a heartbeat.
            # This seems better than current_url or title because they
            # interfere with Chrome developer tools.
            for browser in self.browsers:
                if browser.window_handles is None:
                    # This won't occur (as an exception will be thrown instead)
                    # but to make sure the above condition is evaluated.
                    raise RuntimeError()
        except Exception:
            # Browser exited, or didn't respond.
            self._logger.debug('Browser not responding.')
            self.credit -= 1
            alive = False
        if alive and self.credit < self.max_credit:
            self._logger.info('Browser recovered.')
            self.credit = self.max_credit
        return self.credit > 0
