#!/usr/bin/env python

import logging
import multiprocessing
import time
import traceback

import browser
import kcsapi_util
import proxy_util
import server


COMMAND_RELOAD_KCSAPI = 'reload_kcsapi'


class DummyProcess(object):

    def join(self):
        pass


def control(args):
    # It seems that uncaught exceptions are silently buffered after creating
    # another multiprocessing.Process.
    ps = DummyProcess()
    pk = DummyProcess()
    pc = DummyProcess()
    try:
        logger = logging.getLogger('kcaa.controller')
        har_manager = proxy_util.HarManager(args, 3.0)
        to_exit = multiprocessing.Event()
        controller_conn, server_conn = multiprocessing.Pipe()
        browsers_server_conn, servers_browser_conn = multiprocessing.Pipe()
        ps = multiprocessing.Process(target=server.handle_server,
                                     args=(args, to_exit, controller_conn,
                                           servers_browser_conn))
        ps.start()
        if not server_conn.poll(3.0):
            logger.error('Server is not responding. Shutting down.')
            to_exit.set()
            return
        root_url = server_conn.recv()
        pk = multiprocessing.Process(target=browser.setup_kancolle_browser,
                                     args=(args, browsers_server_conn,
                                           to_exit))
        pc = multiprocessing.Process(target=browser.setup_kcaa_browser,
                                     args=(args, root_url, to_exit))
        pk.start()
        pc.start()
        kcsapi_handler = kcsapi_util.KCSAPIHandler(har_manager)
        while True:
            time.sleep(0.1)
            if to_exit.wait(0.0):
                logger.error('Controller got an exit signal. Shutting down.')
                break
            while server_conn.poll():
                data = server_conn.recv()
                command = data[0]
                if command == COMMAND_RELOAD_KCSAPI:
                    reload(kcsapi_util)
                    kcsapi_handler = kcsapi_util.KCSAPIHandler(har_manager)
                    kcsapi_handler.reload_handlers()
            try:
                for obj in kcsapi_handler.get_updated_objects():
                    server_conn.send((obj.object_type, obj.json()))
            except:
                # Permit an exception in KCSAPI handler -- it's very likely a
                # bug in how a raw response is read.
                # Rather, reload all the handlers to reflect possible bug fixes
                # in source files.
                # Note that you need to catch another exception before seeing
                # the effect of an edit.
                traceback.print_exc()
                reload(kcsapi_util)
                kcsapi_handler = kcsapi_util.KCSAPIHandler(har_manager)
                kcsapi_handler.reload_handlers()
    except:
        traceback.print_exc()
    to_exit.set()
    ps.join()
    pk.join()
    pc.join()
