#!/usr/bin/env python

import argparse


# Converts --debug=true style specs to boolean values.
def string_bool(value):
    try:
        return {
            'true': True,
            'yes': True,
            'false': False,
            'no': False,
        }[value.lower()]
    except KeyError:
        raise ValueError('Invalid value: {}'.format(value))


def parse_args(argv):
    parser = argparse.ArgumentParser(description='KCAA server.')
    parser.add_argument('--proxy_controller', default='localhost:9090',
                        help='Proxy controller address.')
    parser.add_argument('--proxy', default='localhost:9091',
                        help='Proxy address.')
    parser.add_argument('--server_port', default=0, type=int,
                        help='Server port to use.')
    parser.add_argument('--backend_update_interval', default=0.1, type=float,
                        help='Update interval for backend processes, '
                             'including the controller and server.')
    parser.add_argument('--kancolle_browser', default='chrome',
                        choices=['chrome', 'firefox', 'phantomjs'],
                        help='Browser to open Kancolle player.')
    parser.add_argument('--kcaa_browser', default='chrome',
                        choices=['chrome', 'firefox', ''],
                        help='Browser to open KCAA client. You can leave this '
                             'empty if you want to open the KCAA client from '
                             'a different machine.')
    parser.add_argument('--chrome_binary', default='/usr/bin/google-chrome',
                        help='Chrome binary to use. Useful especially when '
                             'you want to use Chromium or Dartium.')
    parser.add_argument('--chromedriver_binary', default='chromedriver',
                        help='Chromedriver binary to use.')
    parser.add_argument('--phantomjs_binary', default='phantomjs',
                        help='PhantomJS binary to use.')
    parser.add_argument('--frontend_update_interval', default=0.5, type=float,
                        help='Update interval for frontend processes, '
                             'including the client.')
    parser.add_argument('--credentials', default='',
                        help='Credentials file to auto-login. The file should '
                             'contain the login ID and password separated by '
                             'colon, in one line. Only DMM account is '
                             'supported.')
    parser.add_argument('--debug', default=False, type=string_bool,
                        help='True if showing various debug information. This '
                             'is useful for developing, but would reduce '
                             'performance.')
    return parser.parse_args(argv)
