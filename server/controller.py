#!/usr/bin/env python

import logging
import multiprocessing
import time

import browser
import kcsapi_util
import proxy_util


def control(args, server_conn, to_exit):
    logger = logging.getLogger('kcaa.controller')
    har_manager = proxy_util.HarManager(args)
    # HarManager first resets the proxy. Notify the server that it's done.
    server_conn.send(True)
    if not server_conn.poll(3.0):
        logger.error('Server is not responding. Shutting down.')
        to_exit.set()
        return
    root_url = server_conn.recv()
    p = multiprocessing.Process(target=browser.setup_kancolle_browser,
                                args=(args, to_exit))
    p.start()
    p = multiprocessing.Process(target=browser.setup_kcaa_browser,
                                args=(args, root_url, to_exit))
    p.start()
    kcsapi_handler = kcsapi_util.KcsapiHandler(har_manager)
    while True:
        time.sleep(1.0)
        if to_exit.wait(0.0):
            logger.error('Controller got an exit signal. Shutting down.')
            break
        for obj in kcsapi_handler.get_updated_objects():
            server_conn.send((obj.object_type, obj.data))
    to_exit.set()
