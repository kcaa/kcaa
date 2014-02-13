#!/usr/bin/env python

import logging
import time

import browser
import kcsapi_util
import proxy_util


def controll(args, server_conn, to_exit):
    logger = logging.getLogger('kcaa.controller')
    har_manager = proxy_util.HarManager(args)
    # HarManager first resets the proxy. Notify the server that it's done.
    server_conn.send(True)
    if not server_conn.poll(3.0):
        logger.error('Server is not responding. Shutting down.')
        to_exit.set()
        return
    root_url = server_conn.recv()
    time.sleep(1.0)
    browser_monitor = browser.setup(args, root_url)
    debug = True
    objects = {}
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
            for api_name, response in kcsapi_util.get_kcsapi_responses(har):
                logger.debug('Accessed KCSAPI: {}'.format(api_name))
                try:
                    for obj in kcsapi_util.dispatch(api_name, response, debug):
                        old_obj = objects.get(obj.object_type)
                        if old_obj is not None:
                            old_obj.update(api_name, obj)
                            obj = old_obj
                        else:
                            objects[obj.object_type] = obj
                        server_conn.send((obj.object_type, obj.data))
                except ValueError as e:
                    logger.debug(e)
    to_exit.set()
