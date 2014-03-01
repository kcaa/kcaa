#!/usr/bin/env python

import logging
import multiprocessing
import time
import traceback

import browser
import kcsapi_util
import manipulator_util
import proxy_util
import server


COMMAND_RELOAD_KCSAPI = 'reload_kcsapi'
COMMAND_MANIPULATE = 'manipulate'


class DummyProcess(object):

    def join(self):
        pass


def control(args):
    # It seems that uncaught exceptions are silently buffered after creating
    # another multiprocessing.Process.
    to_exit = multiprocessing.Event()
    ps = DummyProcess()
    pk = DummyProcess()
    pc = DummyProcess()
    try:
        logger = logging.getLogger('kcaa.controller')
        har_manager = proxy_util.HarManager(args, 3.0)
        controller_conn, server_conn = multiprocessing.Pipe()
        click_queue = multiprocessing.Queue()
        ps = multiprocessing.Process(target=server.handle_server,
                                     args=(args, to_exit, controller_conn))
        ps.start()
        if not server_conn.poll(3.0):
            logger.error('Server is not responding. Shutting down.')
            to_exit.set()
            return
        root_url = server_conn.recv()
        pk = multiprocessing.Process(target=browser.setup_kancolle_browser,
                                     args=(args, click_queue, to_exit))
        pc = multiprocessing.Process(target=browser.setup_kcaa_browser,
                                     args=(args, root_url, to_exit))
        pk.start()
        pc.start()
        kcsapi_handler = kcsapi_util.KCSAPIHandler(har_manager)
        manipulator_manager = manipulator_util.ManipulatorManager(
            click_queue, kcsapi_handler.objects, time.time())
        while True:
            time.sleep(0.1)
            if to_exit.wait(0.0):
                logger.info('Controller got an exit signal. Shutting down.')
                break
            while server_conn.poll():
                data = server_conn.recv()
                command = data[0]
                if command == COMMAND_RELOAD_KCSAPI:
                    serialized_objects = kcsapi_handler.serialize_objects()
                    reload(kcsapi_util)
                    kcsapi_handler = kcsapi_util.KCSAPIHandler(har_manager)
                    kcsapi_handler.reload_handlers()
                    kcsapi_handler.deserialize_objects(serialized_objects)
                    manipulator_manager.objects = kcsapi_handler.objects
                elif command == COMMAND_MANIPULATE:
                    try:
                        manipulator_manager.dispatch(data[1:])
                    except:
                        traceback.print_exc()
            try:
                for obj in kcsapi_handler.get_updated_objects():
                    server_conn.send((obj.object_type, obj.json()))
                manipulator_manager.update(time.time())
            except:
                # Permit an exception in KCSAPI handler or manipulators -- it's
                # very likely a bug in how a raw response is read, or how they
                # are implemented.
                # Do not reload modules automatically because the bug should be
                # still there. You can always reload modules explicitly with
                # the reload button in the KCAA control window.
                traceback.print_exc()
    except:
        traceback.print_exc()
    to_exit.set()
    ps.join()
    pk.join()
    pc.join()
