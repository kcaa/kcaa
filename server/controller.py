#!/usr/bin/env python

import time

import browser


def controll(args, server_conn, to_exit):
    if not server_conn.poll(3.0):
        print 'Server is not responding. Shutting down.'
        to_exit.set()
        return
    root_url = server_conn.recv()
    time.sleep(1.0)
    browser_monitor = browser.setup(args, root_url)
    while True:
        time.sleep(1.0)
        if to_exit.wait(0.0):
            print 'Server dead. Shutting down the browser.'
            browser_monitor.browser.close()
            break
        if not browser_monitor.is_alive():
            print 'Browser dead. Shutting down the server.'
            break
    to_exit.set()
