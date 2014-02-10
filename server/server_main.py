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


def monitor_browser(args, root_url, server_ready, to_exit):
    if not server_ready.wait(3.0):
        print 'Server is not responding. Shutting down.'
        to_exit.set()
        return
    br = browser.setup(args, root_url)
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


def main(argv):
    args = flags.parse_args(argv[1:])
    move_to_client_dir()
    to_exit = multiprocessing.Event()
    server_ready = multiprocessing.Event()
    httpd, root_url = server.setup(args)
    p = multiprocessing.Process(target=monitor_browser,
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
