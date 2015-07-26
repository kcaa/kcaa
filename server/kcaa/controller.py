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


class ControllerState(object):

    def __init__(self, logger, args, to_exit):
        self.logger = logger
        self.args = args
        self.to_exit = to_exit
        self.initialized = False

    def setup(self):
        self.to_exit.clear()
        self.preferences = load_preferences(self.args, self.logger)
        har_manager = proxy_util.HarManager(self.args, 3.0)
        self.controller_conn_for_server, self.server_conn = (
            multiprocessing.Pipe())
        self.object_queue = multiprocessing.Queue()
        self.server_process = multiprocessing.Process(
            target=server.handle_server,
            args=(self.args, self.to_exit, self.controller_conn_for_server,
                  self.object_queue))
        self.server_process.start()
        self.object_queue.put(
            (True, self.preferences.object_type, self.preferences.json()))
        if not self.server_conn.poll(3.0):
            raise Exception('Server is not responding. Shutting down.')
        root_url = self.server_conn.recv()
        self.controller_conn_for_browser, self.browser_conn = (
            multiprocessing.Pipe())
        self.browser_broken = multiprocessing.Event()
        self.kancolle_browser_process = multiprocessing.Process(
            target=browser.setup_kancolle_browser,
            args=(self.args, self.controller_conn_for_browser, self.to_exit,
                  self.browser_broken))
        self.kcaa_browser_process = multiprocessing.Process(
            target=browser.setup_kcaa_browser,
            args=(self.args, root_url, self.to_exit))
        self.kancolle_browser_process.start()
        self.kcaa_browser_process.start()
        self.kcsapi_handler = kcsapi_util.KCSAPIHandler(
            har_manager, self.args.journal_basedir, self.args.state_basedir,
            self.args.debug)
        self.kcsapi_handler.update_preferences(self.preferences)
        self.manipulator_manager = manipulator_util.ManipulatorManager(
            self.browser_conn, self.kcsapi_handler.objects,
            self.kcsapi_handler.loaded_states, self.preferences, time.time())
        self.initialized = True

    def teardown(self):
        self.to_exit.set()
        if not self.initialized:
            return
        self.server_conn.close()
        self.controller_conn_for_server.close()
        self.browser_conn.close()
        self.controller_conn_for_browser.close()
        self.server_process.join()
        self.kancolle_browser_process.join()
        self.kcaa_browser_process.join()
        self.kcsapi_handler.save_journals(self.args.journal_basedir)
        self.kcsapi_handler.save_states(self.args.state_basedir)


def control(args, to_exit):
    # It seems that uncaught exceptions are silently buffered after creating
    # another multiprocessing.Process.
    logenv.setup_logger(args.debug, args.log_file, args.log_level,
                        args.keep_timestamped_logs)
    logger = logging.getLogger('kcaa.controller')
    state = ControllerState(logger, args, to_exit)
    try:
        state.setup()
        preferences, kcsapi_handler, manipulator_manager = (
            state.preferences, state.kcsapi_handler, state.manipulator_manager)
        last_restart = 0
        restart_wait_sec = DEFAULT_RESTART_WAIT_SEC
        while True:
            to_restart = False
            time.sleep(args.backend_update_interval)
            if to_exit.wait(0.0):
                logger.info('Controller got an exit signal. Shutting down.')
                break
            while state.server_conn.poll():
                command_type, command_args = state.server_conn.recv()
                if command_type == COMMAND_REQUEST_OBJECT:
                    try:
                        requestable = kcsapi_handler.request(command_args)
                        if requestable:
                            if isinstance(requestable, str):
                                state.server_conn.send(requestable)
                            else:
                                state.server_conn.send(requestable.json())
                        else:
                            state.server_conn.send(None)
                    except:
                        logger.error(traceback.format_exc())
                        state.server_conn.send(None)
                elif command_type == COMMAND_CLICK:
                    # This command is currently dead. If there is a reasonable
                    # means to get the clicked position in the client, this is
                    # supposed to feed that information to the fake client
                    # owned by the controller to better guess the current
                    # screen.
                    state.browser_conn.send((browser.COMMAND_CLICK, command_args))
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
                        state.browser_conn, kcsapi_handler.objects,
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
                    state.object_queue.put(
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
                    state.browser_conn.send((browser.COMMAND_TAKE_SCREENSHOT,
                                             (format, quality, width, height)))
                    screenshot = state.browser_conn.recv()
                    state.server_conn.send(screenshot)
                else:
                    raise ValueError(
                        'Unknown controller command: type = {}, args = {}'
                        .format(command_type, command_args))
            try:
                for obj in kcsapi_handler.get_updated_objects():
                    state.object_queue.put((True, obj.object_type, obj.json()))
                for obj in manipulator_manager.update(time.time()):
                    state.object_queue.put((True, obj.object_type, obj.json()))
            except kcsapi_util.NoResponseError:
                logger.error('Detected broken KCSAPI response. Will restart.')
                to_restart = True
            except:
                # Permit an exception in KCSAPI handler or manipulators -- it's
                # very likely a bug in how a raw response is read, or how they
                # are implemented.
                # Do not reload modules automatically because the bug should be
                # still there. You can always reload modules explicitly with
                # the reload button in the KCAA control window.
                logger.error(traceback.format_exc())
            if state.browser_broken.wait(0.0):
                logger.error('Detected broken browser. Will restart.')
                to_restart = True
            if to_restart:
                # Some unrecoverable error happened. Retry after some wait.
                # TODO: Maybe restore the currently scheduled manipulators as
                # much as possible, but it should not be critical.
                state.teardown()
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
                state.setup()
                preferences, kcsapi_handler, manipulator_manager = (
                    state.preferences, state.kcsapi_handler,
                    state.manipulator_manager)
                last_restart = time.time()
    except (KeyboardInterrupt, SystemExit):
        logger.info('SIGINT received in the controller process. Exiting...')
    except:
        logger.error(traceback.format_exc())
    state.teardown()
