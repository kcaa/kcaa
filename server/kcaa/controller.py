#!/usr/bin/env python

import logging
import multiprocessing
import os.path
import time
import traceback

import browser
import kcsapi
import kcsapi_util
import logenv
import manipulator_util
import proxy_util
import server


COMMAND_CLICK = 'click'
COMMAND_RELOAD_KCSAPI = 'reload_kcsapi'
COMMAND_RELOAD_MANIPULATORS = 'reload_manipulators'
COMMAND_MANIPULATE = 'manipulate'
COMMAND_TAKE_SCREENSHOT = 'take_screenshot'
COMMAND_SET_PREFERENCES = 'set_preferences'


class DummyProcess(object):

    def join(self):
        pass


def load_preferences(args, logger):
    if not args.preferences:
        logger.info('Preferences file is not specified. Using default.')
        logger.info('If you want to have one, set the value of the flag '
                    '--preferences properly.')
        return kcsapi.prefs.Preferences()
    elif os.path.isfile(args.preferences):
        logger.info(
            'Prefenreces file found at {}. Loading.'.format(args.preferences))
        with open(args.preferences, 'r') as preferences_file:
            preferences = kcsapi.prefs.Preferences.parse_text(
                preferences_file.read())
            return preferences
    else:
        logger.info(
            'Prefenreces file not found at {}. Creating one with default.'
            .format(args.preferences))
        preferences = kcsapi.prefs.Preferences()
        save_preferences(args, logger, preferences)
        return preferences


def save_preferences(args, logger, preferences):
    with open(args.preferences, 'w') as preferences_file:
        preferences_string = preferences.json(
            indent=2, separators=(',', ': '),
            ensure_ascii=False).encode('utf8')
        logger.debug('Saving preferences: ' + preferences_string)
        preferences_file.write(preferences_string)


def control(args, to_exit):
    # It seems that uncaught exceptions are silently buffered after creating
    # another multiprocessing.Process.
    ps = DummyProcess()
    pk = DummyProcess()
    pc = DummyProcess()
    try:
        logenv.setup_logger(args.debug)
        logger = logging.getLogger('kcaa.controller')
        preferences = load_preferences(args, logger)
        har_manager = proxy_util.HarManager(args, 3.0)
        controller_conn, server_conn = multiprocessing.Pipe()
        object_queue = multiprocessing.Queue()
        ps = multiprocessing.Process(target=server.handle_server,
                                     args=(args, to_exit, controller_conn,
                                           object_queue))
        ps.start()
        object_queue.put((preferences.object_type, preferences.json()))
        if not server_conn.poll(3.0):
            logger.error('Server is not responding. Shutting down.')
            to_exit.set()
            return
        root_url = server_conn.recv()
        controller_conn_for_browser, browser_conn = multiprocessing.Pipe()
        pk = multiprocessing.Process(target=browser.setup_kancolle_browser,
                                     args=(args, controller_conn_for_browser,
                                           to_exit))
        pc = multiprocessing.Process(target=browser.setup_kcaa_browser,
                                     args=(args, root_url, to_exit))
        pk.start()
        pc.start()
        kcsapi_handler = kcsapi_util.KCSAPIHandler(
            har_manager, preferences, args.debug)
        manipulator_manager = manipulator_util.ManipulatorManager(
            browser_conn, kcsapi_handler.objects, preferences, time.time())
        while True:
            time.sleep(args.backend_update_interval)
            if to_exit.wait(0.0):
                logger.info('Controller got an exit signal. Shutting down.')
                break
            while server_conn.poll():
                command_type, command_args = server_conn.recv()
                if command_type == COMMAND_CLICK:
                    # This command is currently dead. If there is a reasonable
                    # means to get the clicked position in the client, this is
                    # supposed to feed that information to the fake client
                    # owned by the controller to better guess the current
                    # screen.
                    browser_conn.send((browser.COMMAND_CLICK, command_args))
                elif command_type == COMMAND_RELOAD_KCSAPI:
                    serialized_objects = kcsapi_handler.serialize_objects()
                    reload(kcsapi_util)
                    kcsapi_util.reload_modules()
                    kcsapi_handler = kcsapi_util.KCSAPIHandler(
                        har_manager, args.debug)
                    kcsapi_handler.deserialize_objects(serialized_objects)
                    manipulator_manager.objects = kcsapi_handler.objects
                elif command_type == COMMAND_RELOAD_MANIPULATORS:
                    reload(manipulator_util)
                    manipulator_util.reload_modules()
                    manipulator_manager = manipulator_util.ManipulatorManager(
                        browser_conn, kcsapi_handler.objects, preferences,
                        time.time())
                elif command_type == COMMAND_MANIPULATE:
                    try:
                        manipulator_manager.dispatch(command_args)
                    except:
                        traceback.print_exc()
                elif command_type == COMMAND_SET_PREFERENCES:
                    preferences = kcsapi.prefs.Preferences.parse_text(
                        command_args[0])
                    save_preferences(args, logger, preferences)
                    manipulator_manager.set_auto_manipulator_preferences(
                        kcsapi.prefs.AutoManipulatorPreferences(
                            enabled=preferences.automan_prefs.enabled,
                            schedules=[kcsapi.prefs.ScheduleFragment(
                                start=sf.start, end=sf.end) for sf
                                in preferences.automan_prefs.schedules]))
                elif command_type == COMMAND_TAKE_SCREENSHOT:
                    format, quality, width, height = command_args
                    browser_conn.send((browser.COMMAND_TAKE_SCREENSHOT,
                                       (format, quality, width, height)))
                    screenshot = browser_conn.recv()
                    server_conn.send(screenshot)
                else:
                    raise ValueError(
                        'Unknown controller command: type = {}, args = {}'
                        .format(command_type, command_args))
            try:
                for obj in kcsapi_handler.get_updated_objects():
                    object_queue.put((obj.object_type, obj.json()))
                for obj in manipulator_manager.update(time.time()):
                    object_queue.put((obj.object_type, obj.json()))
            except:
                # Permit an exception in KCSAPI handler or manipulators -- it's
                # very likely a bug in how a raw response is read, or how they
                # are implemented.
                # Do not reload modules automatically because the bug should be
                # still there. You can always reload modules explicitly with
                # the reload button in the KCAA control window.
                traceback.print_exc()
    except (KeyboardInterrupt, SystemExit):
        logger.info('SIGINT received in the controller process. Exiting...')
    except:
        traceback.print_exc()
    to_exit.set()
    ps.join()
    pk.join()
    pc.join()
