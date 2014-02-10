#!/usr/bin/env python

import multiprocessing
import os
import sys
import time

import browser
import flags
import server


def monitor_browser(httpd, args, root_url):
    # To be on the safe side, wait 1 second before creating the first request.
    time.sleep(1.0)
    browser.setup(args, root_url)


def main(argv):
    # Change directory to client directory so that SimpleHTTPServer can serve
    # client resources.
    os.chdir(os.path.join(os.path.dirname(__file__), '..', 'client'))
    args = flags.parse_args(argv[1:])
    httpd, root_url = server.setup(args)
    p = multiprocessing.Process(target=monitor_browser,
                                args=(httpd, args, root_url))
    p.start()
    httpd.serve_forever()


if __name__ == '__main__':
    main(sys.argv)
