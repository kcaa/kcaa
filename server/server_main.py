#!/usr/bin/env python

import argparse
import sys

from selenium import webdriver


def parse_args(argv):
    # TODO: Serve these files from this server.
    url_default = 'http://localhost:3030/kcaa/client/web/index.html'

    parser = argparse.ArgumentParser(description='KCAA server.')
    parser.add_argument('--url', default=url_default,
                        help='Url to open.')
    parser.add_argument('--proxy_controller', default='http://localhost:9090',
                        help='Proxy controller address.')
    parser.add_argument('--browser', default='chrome', choices=['chrome'],
                        help='Browser to use.')
    parser.add_argument('--chrome_binary', default='/usr/bin/google-chrome',
                        help='Chrome binary to use. Useful especially when '
                        'you want to use Chromium or Dartium.')
    parser.add_argument('--chromedriver_binary', default='chromedriver',
                        help='Chromedriver binary to use.')
    return parser.parse_args(argv)


def setup(args):
    browser = None
    if args.browser == 'chrome':
        browser = setup_chrome(args)
    else:
        raise ValueError('Unrecognized browser: {browser}'.format(
            browser=args.browser))
    browser.get(args.url)


def setup_chrome(args):
    options = webdriver.ChromeOptions()
    options.binary_location = args.chrome_binary
    return webdriver.Chrome(executable_path=args.chromedriver_binary,
                            chrome_options=options)


def main(argv):
    args = parse_args(argv[1:])
    setup(args)


if __name__ == '__main__':
    main(sys.argv)
