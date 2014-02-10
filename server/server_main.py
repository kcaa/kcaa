#!/usr/bin/env python

import SimpleHTTPServer
import SocketServer
import multiprocessing
import os
import sys
import time

import browser
import flags


class KcaaHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_HEAD(self):
        # Note: HTTP request handlers are not new-style classes.
        # super() cannot be used.
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_HEAD(self)

    def do_GET(self):
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)


def monitor_browser(httpd, args, url):
    # To be on the safe side, wait 1 second before creating the first request.
    time.sleep(1.0)
    browser.setup(args, url)


def main(argv):
    # Change directory to client directory so that SimpleHTTPServer can serve
    # client resources.
    os.chdir(os.path.join(os.path.dirname(__file__), '..', 'client'))
    args = flags.parse_args(argv[1:])
    httpd = SocketServer.TCPServer(('', args.server_port),
                                   KcaaHTTPRequestHandler)
    _, port = httpd.server_address
    url = 'http://127.0.0.1:{}/web/'.format(port)
    print 'KCAA server listening at {}'.format(url)
    p = multiprocessing.Process(target=monitor_browser,
                                args=(httpd, args, url))
    p.start()
    httpd.serve_forever()


if __name__ == '__main__':
    main(sys.argv)
