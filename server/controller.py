#!/usr/bin/env python

import logging
import time

import browser
import kcsapi_util
import proxy_util


def controll(args, server_conn, to_exit):
    logger = logging.getLogger('kcaa.controller')
    if not server_conn.poll(3.0):
        logger.error('Server is not responding. Shutting down.')
        to_exit.set()
        return
    root_url = server_conn.recv()
    time.sleep(1.0)
    browser_monitor = browser.setup(args, root_url)
    har_manager = proxy_util.HarManager(args)
    while True:
        time.sleep(1.0)
        if to_exit.wait(0.0):
            logger.error('Server dead. Shutting down the browser.')
            browser_monitor.browser.close()
            break
        if not browser_monitor.is_alive():
            logger.info('Browser dead. Shutting down the server.')
            break
        har = har_manager.get_next_page()
        if har:
            for entry in kcsapi_util.get_kcsapi_entries(har):
                logger.debug('KCSAPI URL: {}'.format(entry['request']['url']))
                server_conn.send(entry)
    to_exit.set()
