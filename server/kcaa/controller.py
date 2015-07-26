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


COMMAND_REQUEST_OBJECT = 'request_object'
COMMAND_CLICK = 'click'
COMMAND_RELOAD_KCSAPI = 'reload_kcsapi'
COMMAND_RELOAD_MANIPULATORS = 'reload_manipulators'
COMMAND_MANIPULATE = 'manipulate'
COMMAND_TAKE_SCREENSHOT = 'take_screenshot'
COMMAND_SET_PREFERENCES = 'set_preferences'

# Default wait in seconds before starting in case of network errors.
# If a restart failed, this will be doubled each time.
DEFAULT_RESTART_WAIT_SEC = 6
# If this duration in seconds passed after a restart, the last restart is
# considered as a success.
HEALTHY_DURATION_FOR_RESTART_SUCCESS_SEC = 600


class DummyProcess(object):

    def join(self):
        pass


def load_preferences(args, logger):
    if not args.preferences:
        logger.info('Preferences file is not specified. Using default.')
        logger.info('If you want to have one, set the value of the flag '
                    '--preferences properly.')
        preferences = kcsapi.prefs.Preferences()
        preferences.initialize()
        return preferences
    elif os.path.isfile(args.preferences):
        logger.info(
            'Prefenreces file found at {}. Loading.'.format(args.preferences))
        with open(args.preferences, 'r') as preferences_file:
            preferences = kcsapi.prefs.Preferences.parse_text(
                preferences_file.read())
            preferences.initialize()
            return preferences
    else:
        logger.info(
            'Prefenreces file not found at {}. Creating one with default.'
            .format(args.preferences))
        preferences = kcsapi.prefs.Preferences()
        preferences.initialize()
        save_preferences(args, logger, preferences)
        return preferences


def save_preferences(args, logger, preferences):
    with open(args.preferences, 'w') as preferences_file:
        preferences_string = preferences.json(
            indent=2, separators=(',', ': '), sort_keys=True,
            ensure_ascii=False).encode('utf8')
        preferences_file.write(preferences_string)


def setup(logger, args, to_exit):
    to_exit.clear()
    preferences = load_preferences(args, logger)
    har_manager = proxy_util.HarManager(args, 3.0)
    controller_conn, server_conn = multiprocessing.Pipe()
    object_queue = multiprocessing.Queue()
    ps = multiprocessing.Process(target=server.handle_server,
                                 args=(args, to_exit, controller_conn,
                                       object_queue))
    ps.start()
    object_queue.put((True, preferences.object_type, preferences.json()))
    if not server_conn.poll(3.0):
        raise Exception('Server is not responding. Shutting down.')
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
        har_manager, args.journal_basedir, args.state_basedir, args.debug)
    kcsapi_handler.update_preferences(preferences)
    manipulator_manager = manipulator_util.ManipulatorManager(
        browser_conn, kcsapi_handler.objects, kcsapi_handler.loaded_states,
        preferences, time.time())
    return (preferences, kcsapi_handler, manipulator_manager, server_conn,
            browser_conn, object_queue, ps, pk, pc)


def teardown(kcsapi_handler, args, to_exit, ps, pk, pc):
    to_exit.set()
    ps.join()
    pk.join()
    pc.join()
    if kcsapi_handler:
        kcsapi_handler.save_journals(args.journal_basedir)
        kcsapi_handler.save_states(args.state_basedir)


def control(args, to_exit):
    # It seems that uncaught exceptions are silently buffered after creating
    # another multiprocessing.Process.
    ps = DummyProcess()
    pk = DummyProcess()
    pc = DummyProcess()
    kcsapi_handler = None
    try:
        logenv.setup_logger(args.debug, args.log_file, args.log_level,
                            args.keep_timestamped_logs)
        logger = logging.getLogger('kcaa.controller')
        (preferences, kcsapi_handler, manipulator_manager, server_conn,
            browser_conn, object_queue, ps, pk, pc) = setup(
                logger, args, to_exit)
        last_restart = 0
        restart_wait_sec = DEFAULT_RESTART_WAIT_SEC
        while True:
            time.sleep(args.backend_update_interval)
            if to_exit.wait(0.0):
                logger.info('Controller got an exit signal. Shutting down.')
                break
            while server_conn.poll():
                command_type, command_args = server_conn.recv()
                if command_type == COMMAND_REQUEST_OBJECT:
                    try:
                        requestable = kcsapi_handler.request(command_args)
                        if requestable:
                            if isinstance(requestable, str):
                                server_conn.send(requestable)
                            else:
                                server_conn.send(requestable.json())
                        else:
                            server_conn.send(None)
                    except:
                        logger.error(traceback.format_exc())
                        server_conn.send(None)
                elif command_type == COMMAND_CLICK:
                    # This command is currently dead. If there is a reasonable
                    # means to get the clicked position in the client, this is
                    # supposed to feed that information to the fake client
                    # owned by the controller to better guess the current
                    # screen.
                    browser_conn.send((browser.COMMAND_CLICK, command_args))
                elif command_type == COMMAND_RELOAD_KCSAPI:
                    kcsapi_handler.save_journals(args.journal_basedir)
                    kcsapi_handler.save_states(args.state_basedir)
                    serialized_objects = kcsapi_handler.serialize_objects()
                    reload(kcsapi_util)
                    kcsapi_util.reload_modules()
                    kcsapi_handler = kcsapi_util.KCSAPIHandler(
                        har_manager, args.journal_basedir, args.state_basedir,
                        args.debug)
                    kcsapi_handler.deserialize_objects(serialized_objects)
                    manipulator_manager.reset_objects(
                        kcsapi_handler.objects, kcsapi_handler.loaded_states)
                    # TODO: Refactor!
                    preferences = kcsapi_handler.objects['Preferences']
                    manipulator_manager.preferences = preferences
                elif command_type == COMMAND_RELOAD_MANIPULATORS:
                    reload(manipulator_util)
                    manipulator_util.reload_modules()
                    manipulator_manager = manipulator_util.ManipulatorManager(
                        browser_conn, kcsapi_handler.objects,
                        kcsapi_handler.loaded_states, preferences, time.time())
                elif command_type == COMMAND_MANIPULATE:
                    try:
                        manipulator_manager.dispatch(command_args)
                    except:
                        logger.error(traceback.format_exc())
                elif command_type == COMMAND_SET_PREFERENCES:
                    preferences = kcsapi.prefs.Preferences.parse_text(
                        command_args[0])
                    save_preferences(args, logger, preferences)
                    # TODO: Refactor this part. Generalize the framework to
                    # update objects.
                    kcsapi_handler.update_preferences(preferences)
                    object_queue.put(
                        (False, 'Preferences', preferences.json()))
                    manipulator_manager.set_auto_manipulator_preferences(
                        kcsapi.prefs.AutoManipulatorPreferences(
                            enabled=preferences.automan_prefs.enabled,
                            schedules=[kcsapi.prefs.ScheduleFragment(
                                start=sf.start, end=sf.end) for sf
                                in preferences.automan_prefs.schedules]))
                    # TODO: Refactor this as well. Setting Preferences object
                    # should be a single operation on ManipulatorManager.
                    manipulator_manager.preferences = preferences
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
                    object_queue.put((True, obj.object_type, obj.json()))
                for obj in manipulator_manager.update(time.time()):
                    object_queue.put((True, obj.object_type, obj.json()))
            except kcsapi_util.NoResponseError:
                # Some unrecoverable error happened. Retry after some wait.
                logger.error(traceback.format_exc())
                # TODO: Maybe restore the currently scheduled manipulators as
                # much as possible, but it should not be critical.
                teardown(kcsapi_handler, args, to_exit, ps, pk, pc)
                now = time.time()
                if (now - last_restart <
                        HEALTHY_DURATION_FOR_RESTART_SUCCESS_SEC):
                    logger.error('Last restart seems to have failed.')
                    restart_wait_sec *= 2
                else:
                    logger.info('Last restart seems to have succeeded.')
                    restart_wait_sec = DEFAULT_RESTART_WAIT_SEC
                logger.info(
                    'Waiting for {} seconds before restarting...'.format(
                        restart_wait_sec))
                time.sleep(restart_wait_sec)
                logger.info('Restarting the browsers.')
                (preferences, kcsapi_handler, manipulator_manager, server_conn,
                    browser_conn, object_queue, ps, pk, pc) = setup(
                        logger, args, to_exit)
                last_restart = time.time()
            except:
                # Permit an exception in KCSAPI handler or manipulators -- it's
                # very likely a bug in how a raw response is read, or how they
                # are implemented.
                # Do not reload modules automatically because the bug should be
                # still there. You can always reload modules explicitly with
                # the reload button in the KCAA control window.
                logger.error(traceback.format_exc())
    except (KeyboardInterrupt, SystemExit):
        logger.info('SIGINT received in the controller process. Exiting...')
    except:
        logger.error(traceback.format_exc())
    teardown(kcsapi_handler, args, to_exit, ps, pk, pc)
