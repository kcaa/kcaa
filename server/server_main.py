#!/usr/bin/env python

import multiprocessing
import os
import sys
import time

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


def monitor_browser(args, root_url, to_exit):
    # To be on the safe side, wait 1 second before creating the first request.
    time.sleep(1.0)
    br = browser.setup(args, root_url)
    try:
        running = True
        while running:
            time.sleep(1.0)
            running = br.current_url is not None
            if to_exit.wait(0.0):
                running = False
    except Exception:
        print 'Browser exited. Shutting down server...'
        to_exit.set()


def main(argv):
    args = flags.parse_args(argv[1:])
    move_to_client_dir()
    to_exit = multiprocessing.Event()
    httpd, root_url = server.setup(args)
    p = multiprocessing.Process(target=monitor_browser,
                                args=(args, root_url, to_exit))
    p.start()
    httpd.timeout = 1.0
    while True:
        httpd.handle_request()
        if to_exit.wait(0.0):
            break
    to_exit.set()
    p.join()


if __name__ == '__main__':
    main(sys.argv)
