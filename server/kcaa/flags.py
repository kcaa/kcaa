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
                        choices=['chrome', 'chromium', 'firefox', 'phantomjs'],
                        help='Browser to open Kancolle player.')
    parser.add_argument('--kcaa_browser', default='chrome',
                        choices=['chrome', 'chromium', 'firefox', ''],
                        help='Browser to open KCAA client. You can leave this '
                             'empty if you want to open the KCAA client from '
                             'a different machine.')
    parser.add_argument('--show_kancolle_screen', default=False,
                        type=string_bool,
                        help='True if showing Kancolle screen in KCAA client. '
                             'Useful if you open the KCAA client from a '
                             'different machine. You might want to pass '
                             '"--kcaa_browswer= '
                             '--kancolle_browswer=phantomjs" for best '
                             'performance.')
    parser.add_argument('--chrome_binary', default='',
                        help='Chrome binary to use. Usually you do not need '
                             'to set a value.')
    parser.add_argument('--chromium_binary', default='',
                        help='Chromium binary to use. Also accepts Dartium.')
    parser.add_argument('--chrome_user_data_basedir', default='',
                        help='Base directory for storing Chrome user data. '
                             'If left empty, all user-specific configuration '
                             'will be lost when a browser exits.')
    parser.add_argument('--chromedriver_binary', default='chromedriver',
                        help='Chromedriver binary to use.')
    parser.add_argument('--phantomjs_binary', default='phantomjs',
                        help='PhantomJS binary to use.')
    parser.add_argument('--frontend_update_interval', default=0.5, type=float,
                        help='Update interval for frontend processes, '
                             'including the client.')
    parser.add_argument('--preferences', default='',
                        help='File describes user preferences in JSON. If not '
                             'present, a new file with default values will be '
                             'created.')
    parser.add_argument('--journal_basedir', default='',
                        help='Base directory where journal data is stored.'
                             'If not existent, a new one will be created.')
    parser.add_argument('--state_basedir', default='',
                        help='Base directory where state data is stored.'
                             'If not existent, a new one will be created.')
    parser.add_argument('--credentials', default='',
                        help='Credentials file to auto-login. The file should '
                             'contain the login ID and password separated by '
                             'colon, in one line. Only DMM account is '
                             'supported.')
    parser.add_argument('--debug', default=False, type=string_bool,
                        help='True if showing various debug information. This '
                             'is useful for developing, but would reduce '
                             'performance.')
    parser.add_argument('--log_file', default='log.txt',
                        help='Log file. If empty, no log will be written but '
                             'you usually should avoid it as the debug log '
                             'really helps when a problem arises.')
    parser.add_argument('--log_level', default='DEBUG',
                        help='Log level. Usually this should be DEBUG to '
                             'help debugging an issue later.')
    parser.add_argument('--keep_timestamped_logs', default=False,
                        type=string_bool,
                        help='Keep the timestamped logs instead of '
                        'overwriting the log file. The output log file will '
                        'be <--log_file>.<YYMMDDhhmmss>.')
    return parser.parse_args(argv)
