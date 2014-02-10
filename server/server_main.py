#!/usr/bin/env python

import multiprocessing
import os
import sys

import browser
import flags
import server


DEPLOYED_PACKAGE = 'build'
DEVELOPMENT_PACKAGE = 'web'


def move_to_client_dir():
    # Change directory to client directory so that SimpleHTTPServer can serve
    # client resources.
    client_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
                                              'client'))
    if not os.path.isdir(client_dir):
        raise IOError('No client directory found: {}'.format(client_dir))
    os.chdir(client_dir)
    # Use 'build' subdirectory when deployed, or 'web' when being developed.
    if os.path.isdir(DEPLOYED_PACKAGE):
        os.chdir(DEPLOYED_PACKAGE)
    elif os.path.isdir(DEVELOPMENT_PACKAGE):
        os.chdir(DEVELOPMENT_PACKAGE)
    else:
        raise IOError('No client package directories found under {}.'.format(
            client_dir))


def main(argv):
    args = flags.parse_args(argv[1:])
    move_to_client_dir()
    to_exit = multiprocessing.Event()
    server_ready = multiprocessing.Event()
    httpd, root_url = server.setup(args)
    p = multiprocessing.Process(target=browser.monitor_browser,
                                args=(args, root_url, server_ready, to_exit))
    p.start()
    httpd.timeout = 1.0
    while True:
        httpd.handle_request()
        server_ready.set()
        if to_exit.wait(0.0):
            break
    to_exit.set()
    p.join()


if __name__ == '__main__':
    main(sys.argv)
