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


def setup(args, url):
    desired_capabilities = get_desired_capabilities(args)
    browser = None
    if args.browser == 'chrome':
        browser = setup_chrome(args, desired_capabilities)
    elif args.browser == 'firefox':
        browser = setup_firefox(args, desired_capabilities)
    else:
        raise ValueError('Unrecognized browser: {browser}'.format(
            browser=args.browser))
    browser.set_window_size(1000, 800)
    browser.get(KANCOLLE_URL)
    return BrowserMonitor(browser, 5)


class BrowserMonitor(object):

    def __init__(self, browser, max_credit):
        self._logger = logging.getLogger('kcaa.browser')
        self.browser = browser
        self.max_credit = max_credit
        self.credit = max_credit

    def is_alive(self):
        try:
            # Check window_handles as a heartbeat.
            # This seems better than current_url or title because they
            # interfere with Chrome developer tools.
            if self.browser.window_handles is None:
                # This won't occur (as an exception will be thrown instead)
                # but to make sure the above condition is evaluated.
                self.credit -= 1
                self._logger.debug(
                    'Browser is alive, but no window available?')
            else:
                if self.credit < self.max_credit:
                    self._logger.info('Browser recovered.')
                self.credit = self.max_credit
        except Exception:
            # Browser exited, or didn't respond.
            self._logger.debug('Browser not responding.')
            self.credit -= 1
        return self.credit > 0
