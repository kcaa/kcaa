#!/usr/bin/env python

import argparse


def parse_args(argv):
    parser = argparse.ArgumentParser(description='KCAA server.')
    parser.add_argument('--proxy_controller', default='localhost:9090',
                        help='Proxy controller address.')
    parser.add_argument('--proxy', default='localhost:9091',
                        help='Proxy address.')
    parser.add_argument('--server_port', default=0, type=int,
                        help='Server port to use.')
    parser.add_argument('--browser', default='chrome',
                        choices=['chrome', 'firefox'],
                        help='Browser to use.')
    parser.add_argument('--chrome_binary', default='/usr/bin/google-chrome',
                        help='Chrome binary to use. Useful especially when '
                        'you want to use Chromium or Dartium.')
    parser.add_argument('--chromedriver_binary', default='chromedriver',
                        help='Chromedriver binary to use.')
    return parser.parse_args(argv)