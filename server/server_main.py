#!/usr/bin/env python

import argparse
import sys

from selenium import webdriver


def parse_args(argv):
    # TODO: Serve these files from this server.
    url_default = 'http://127.0.0.1:3030/kcaa/client/web/index.html'

    parser = argparse.ArgumentParser(description='KCAA server.')
    parser.add_argument('--url', default=url_default,
                        help='Url to open.')
    parser.add_argument('--proxy_controller', default='localhost:9090',
                        help='Proxy controller address.')
    parser.add_argument('--proxy', default='localhost:9091',
                        help='Proxy address.')
    parser.add_argument('--browser', default='chrome',
                        choices=['chrome', 'firefox'],
                        help='Browser to use.')
    parser.add_argument('--chrome_binary', default='/usr/bin/google-chrome',
                        help='Chrome binary to use. Useful especially when '
                        'you want to use Chromium or Dartium.')
    parser.add_argument('--chromedriver_binary', default='chromedriver',
                        help='Chromedriver binary to use.')
    return parser.parse_args(argv)


def setup_browser(args):
    desired_capabilities = get_desired_capabilities(args)
    browser = None
    if args.browser == 'chrome':
        browser = setup_chrome(args, desired_capabilities)
    elif args.browser == 'firefox':
        browser = setup_firefox(args, desired_capabilities)
    else:
        raise ValueError('Unrecognized browser: {browser}'.format(
            browser=args.browser))
    browser.get(args.url)
    return browser


def get_desired_capabilities(args):
    capabilities = {}
    capabilities['proxy'] = {'httpProxy': args.proxy,
                             'ftpProxy': args.proxy,
                             'sslProxy': args.proxy,
                             'noProxy': None,
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


def main(argv):
    args = parse_args(argv[1:])
    setup_browser(args)


if __name__ == '__main__':
    main(sys.argv)
