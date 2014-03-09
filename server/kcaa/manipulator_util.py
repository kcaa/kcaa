#!/usr/bin/env python

import logging

import browser
import manipulators
import screens
import task


def reload_modules():
    reload(manipulators)
    manipulators.reload_modules()


class ScreenManager(object):

    def __init__(self, manipulator_manager):
        self._logger = logging.getLogger('kcaa.manipulator_util')
        self.objects = manipulator_manager.objects
        self.updated_object_types = manipulator_manager.updated_object_types
        self.browser_conn = manipulator_manager.browser_conn
        self.task_manager = manipulator_manager.task_manager
        self._last_screen_id = screens.UNKNOWN
        self._current_screen = manipulators.screen.Screen(self)
        self.define_screens()

    def define_screens(self):
        self.screens = {
            screens.SPECIAL_START: manipulators.screen.StartScreen,
            screens.PORT: manipulators.screen.PortScreen,
            screens.PORT_MAIN: manipulators.screen.PortMainScreen,
            screens.PORT_LOGISTICS: manipulators.screen.PortLogisticsScreen,
            screens.MISSION_RESULT: manipulators.screen.MissionResultScreen,
        }

    def click(self, x, y):
        self.browser_conn.send((browser.COMMAND_CLICK, (x, y)))

    def add_task(self, t):
        return self.task_manager.add(t)

    @property
    def current_screen(self):
        return self._current_screen

    def update_screen(self):
        screen_object = self.objects.get('Screen')
        if not screen_object:
            return
        screen_id = screen_object.screen
        if screen_id != self._last_screen_id:
            screen = self.screens.get(screen_id)
            if screen:
                self._current_screen = screen(self)
                self._logger.debug('Current screen is {}'.format(screen_id))
            else:
                self._logger.warn('Current screen {} is not manipulatable.'
                    .format(screen_id))
                self._current_screen = manipulators.screen.Screen(self)
        self._last_screen_id = screen_id


class ManipulatorManager(object):
    """Creates Kancolle manipulator, which assists user interaction by
    manipulating the Kancolle player (Flash) programatically."""

    def __init__(self, browser_conn, objects, epoch):
        self.browser_conn = browser_conn
        self.objects = objects
        self.initialize(epoch)

    def initialize(self, epoch):
        # TODO: Use Queue.Queue?
        self.queue = []
        self.running_auto_triggerer = []
        self.current_task = None
        self.updated_object_types = set()
        self.task_manager = task.TaskManager(epoch)
        self.screen_manager = ScreenManager(self)
        self.define_manipulators()
        self.define_auto_manipulators()
        self.add_initial_auto_manipulators()

    def define_manipulators(self):
        self.manipulators = {
            # Logistics
            'FleetCharge': manipulators.logistics.FleetCharge,
        }

    def define_auto_manipulators(self):
        self.auto_manipulators = {
            # Logistics
            'AutoFleetCharge': manipulators.logistics.AutoFleetCharge,
            # Special
            'AutoStartGame': manipulators.special.AutoStartGame,
            # Auto mission
            'AutoCheckMissionResult':
            manipulators.mission.AutoCheckMissionResult,
        }

    def add_initial_auto_manipulators(self):
        # The order matters. Be sure to start from preferred auto manipulators.
        # If there is at least 1 pending manipulator in the queue, the
        # triggerer won't add another one.
        initial_auto_manipulators = [
            'AutoCheckMissionResult',
            'AutoFleetCharge',
            'AutoStartGame',
        ]
        for name in initial_auto_manipulators:
            self.add_auto_manipulator(self.auto_manipulators[name])

    def add_manipulator(self, manipulator):
        t = self.task_manager.add(manipulator)
        t.suspend()
        self.queue.append(t)
        return t

    def add_auto_manipulator(self, auto_manipulator):
        t = self.task_manager.add(manipulators.base.AutoManipulatorTriggerer(
            self, auto_manipulator))
        self.running_auto_triggerer.append(t)
        return t

    def update(self, current):
        """Update manipulators.

        :param float current: Current time in seconds
        :returns: Updated KCSAPI objects
        :rtype: :class:`class:`kcaa.kcsapi.model.KCAAObject`
        """
        self.screen_manager.update_screen()
        if not self.current_task:
            if self.queue:
                t = self.queue[0]
                del self.queue[0]
                self.current_task = t
                t.resume()
                for t in self.running_auto_triggerer:
                    t.suspend()
                self.browser_conn.send((browser.COMMAND_COVER, (True,)))
            else:
                self.current_task = None
                previously_run = False
                for t in self.running_auto_triggerer:
                    if not t.running:
                        t.resume()
                        previously_run = True
                if previously_run:
                    self.browser_conn.send((browser.COMMAND_COVER, (False,)))
        else:
            for t in self.running_auto_triggerer:
                t.suspend()
        self.task_manager.update(current)
        if self.current_task not in self.task_manager.tasks:
            self.current_task = None
        updated_objects = [self.objects[object_type] for object_type in
                           self.updated_object_types]
        self.updated_object_types.clear()
        return updated_objects

    def dispatch(self, command):
        if len(command) != 2:
            raise ValueError(
                'Command should have the type and args: {}'.format(command))
        command_type, command_args = command
        manipulator = self.manipulators.get(command_type)
        if manipulator:
            try:
                self.add_manipulator(manipulator(self, **command_args))
            except TypeError:
                raise TypeError(
                    'manipulator argument mismatch. type = {}, args = {}'
                    .format(command_type, command_args))
        else:
            raise ValueError('Unknown command type: {}'.format(command_type))
