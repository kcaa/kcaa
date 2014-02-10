#!/usr/bin/env python

import time

from selenium import webdriver


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
    browser.get(url)
    return browser


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


def monitor_browser(args, server_conn, to_exit):
    if not server_conn.poll(3.0):
        print 'Server is not responding. Shutting down.'
        to_exit.set()
        return
    root_url = server_conn.recv()
    time.sleep(1.0)
    br = setup(args, root_url)
    credit = 5
    while credit > 0:
        try:
            time.sleep(1.0)
            if to_exit.wait(0.0):
                break
            # Check window_handles as a heartbeat.
            # This seems better than current_url or title because they
            # interfere with Chrome developer tools.
            if br.window_handles is None:
                # This actually never happens, but kept to ensure
                # br.window_handles is evaluated.
                credit -= 1
            else:
                if credit < 5:
                    print 'Browser recovered.'
                credit = 5
        except Exception:
            # Browser exited, or didn't respond.
            print 'Browser didn\'t responded. Retrying...'
            credit -= 1
    if credit == 0:
        print 'Browser exited. Shutting down server...'
    to_exit.set()
