#!/usr/bin/env python

import datetime
import logging

import browser
from kcaa import kcsapi
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
            screens.PORT_RECORD: manipulators.screen.PortScreen,
            screens.PORT_ENCYCLOPEDIA: manipulators.screen.PortScreen,
            screens.PORT_ITEMRACK: manipulators.screen.PortScreen,
            screens.PORT_FURNITURE: manipulators.screen.PortScreen,
            screens.PORT_QUESTLIST: manipulators.screen.PortScreen,
            screens.PORT_ITEMSHOP: manipulators.screen.PortScreen,
            screens.PORT_EXPEDITION: manipulators.screen.PortScreen,
            screens.PORT_PRACTICE: manipulators.screen.PortScreen,
            screens.PORT_MISSION: manipulators.screen.PortMissionScreen,
            screens.PORT_ORGANIZING: manipulators.screen.PortOrganizingScreen,
            screens.PORT_LOGISTICS: manipulators.screen.PortLogisticsScreen,
            screens.PORT_REBUILDING: manipulators.screen.PortOperationsScreen,
            screens.PORT_REPAIR: manipulators.screen.PortOperationsScreen,
            screens.PORT_SHIPYARD: manipulators.screen.PortOperationsScreen,
            screens.MISSION_RESULT: manipulators.screen.MissionResultScreen,
        }

    def click(self, x, y):
        self.browser_conn.send((browser.COMMAND_CLICK, (x, y)))

    def add_task(self, t):
        return self.task_manager.add(t)

    @property
    def current_screen(self):
        return self._current_screen

    def update_screen(self, screen_id=None):
        screen_object = self.objects.get('Screen')
        if not screen_object:
            return
        if screen_id is None:
            screen_id = screen_object.screen
        else:
            screen_object.screen = screen_id
            self.updated_object_types.add('Screen')
        if screen_id != self._last_screen_id:
            screen = self.screens.get(screen_id)
            if screen:
                self._current_screen = screen(self)
                self._logger.debug('Current screen is {}'.format(screen_id))
            else:
                self._logger.debug('Current screen {} is not manipulatable.'
                    .format(screen_id))
                self._current_screen = manipulators.screen.Screen(self)
        self._last_screen_id = screen_id


class ManipulatorManager(object):
    """Creates Kancolle manipulator, which assists user interaction by
    manipulating the Kancolle player (Flash) programatically."""

    def __init__(self, browser_conn, objects, preferences, epoch):
        self._logger = logging.getLogger('kcaa.manipulator_util')
        self.browser_conn = browser_conn
        self.objects = objects
        self.preferences = preferences
        self.initialize(epoch)

    def initialize(self, epoch):
        # TODO: Use Queue.Queue?
        self.queue = []
        self.running_auto_triggerer = []
        self.current_task = None
        self.last_task = None
        self.updated_object_types = set()
        self.task_manager = task.TaskManager(epoch)
        self.screen_manager = ScreenManager(self)
        self.define_manipulators()
        self.define_auto_manipulators()
        self.add_initial_auto_manipulators()
        self.current_schedule_fragment = None
        self.rmo = kcsapi.client.RunningManipulators()
        self.rmo_last_generation = self.rmo.generation
        self.objects['RunningManipulators'] = self.rmo
        self.set_auto_manipulator_preferences(self.preferences.automan_prefs)

    def define_manipulators(self):
        self.manipulators = {
            # Mission
            'GoOnMission': manipulators.mission.GoOnMission,
            # Organizing
            'LoadFleet': manipulators.organizing.LoadFleet,
            # Logistics
            'FleetCharge': manipulators.logistics.FleetCharge,
        }

    def define_auto_manipulators(self):
        self.auto_manipulators = {
            # Logistics
            'AutoFleetCharge': manipulators.logistics.AutoFleetCharge,
            # Special
            'AutoStartGame': manipulators.special.AutoStartGame,
            # Mission
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
        self.suppress_auto_manipulators()

    def set_auto_manipulator_preferences(self, automan_prefs):
        self.auto_manipulators_enabled = automan_prefs.enabled
        self._logger.info('AutoManipulator {}.'.format(
            'enabled' if automan_prefs.enabled else 'disabled'))
        self.auto_manipulators_schedules = automan_prefs.schedules
        self._logger.info(
            'AutoManipulator schedules: {}.'.format(automan_prefs.schedules))
        now = datetime.datetime.now()
        seconds_in_today = 3600 * now.hour + 60 * now.minute + now.second
        self._logger.info('Current time: {}'.format(seconds_in_today))
        self.current_schedule_fragment = None
        # Update RunningManipulators object.
        self.rmo.auto_manipulators_enabled = automan_prefs.enabled
        self.rmo.auto_manipulators_active = (
            self.are_auto_manipulator_scheduled())
        self.rmo.generation += 1

    @staticmethod
    def in_schedule_fragment(seconds_in_today, schedule_fragment):
        if (seconds_in_today >= schedule_fragment.start and
                seconds_in_today < schedule_fragment.end):
            return True

    def are_auto_manipulator_scheduled(self, seconds_in_today=None):
        if not self.auto_manipulators_enabled:
            return False
        if seconds_in_today is None:
            now = datetime.datetime.now()
            seconds_in_today = 3600 * now.hour + 60 * now.minute + now.second
        if self.current_schedule_fragment:
            if ManipulatorManager.in_schedule_fragment(
                    seconds_in_today, self.current_schedule_fragment):
                return True
        self.current_schedule_fragment = None
        for schedule_fragment in self.auto_manipulators_schedules:
            if ManipulatorManager.in_schedule_fragment(seconds_in_today,
                                                       schedule_fragment):
                self.current_schedule_fragment = schedule_fragment
                return True
        return False

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

    def leave_port(self):
        if isinstance(self.screen_manager.current_screen,
                      manipulators.screen.PortScreen):
            self.screen_manager.update_screen(screens.PORT)

    def resume_auto_manipulators(self):
        previously_run = True
        for t in self.running_auto_triggerer:
            if not t.running:
                t.resume()
                previously_run = False
        return not previously_run

    def suppress_auto_manipulators(self):
        previously_run = False
        for t in self.running_auto_triggerer:
            if t.running:
                t.suspend()
                previously_run = True
        return previously_run

    def update(self, current):
        """Update manipulators.

        :param float current: Current time in seconds
        :returns: Updated KCSAPI objects
        :rtype: :class:`class:`kcaa.kcsapi.model.KCAAObject`
        """
        self.screen_manager.update_screen()
        if self.current_task:
            self.suppress_auto_manipulators()
        else:
            if self.queue:
                t = self.queue[0]
                del self.queue[0]
                self.current_task = t
                t.resume()
                self.suppress_auto_manipulators()
                if not self.last_task:
                    self.browser_conn.send((browser.COMMAND_COVER, (True,)))
                    self.leave_port()
                self.rmo.running_manipulator = unicode(
                    self.current_task.__class__.__name__, 'utf8')
                self.rmo.manipulators_in_queue = [
                    unicode(manipulator.__class__.__name__, 'utf8')
                    for manipulator in self.queue]
                self.rmo.generation += 1
            else:
                if self.last_task:
                    self.browser_conn.send((browser.COMMAND_COVER, (False,)))
                    self.rmo.running_manipulator = None
                    self.rmo.manipulators_in_queue = []
                    self.rmo.generation += 1
                self.current_task = None
                self.last_task = None
                if self.are_auto_manipulator_scheduled():
                    if self.resume_auto_manipulators():
                        self.leave_port()
                        self.rmo.auto_manipulators_active = True
                        self.rmo.generation += 1
                else:
                    if self.suppress_auto_manipulators():
                        self.rmo.auto_manipulators_active = False
                        self.rmo.generation += 1
        self.task_manager.update(current)
        if self.current_task not in self.task_manager.tasks:
            self.last_task = self.current_task
            self.current_task = None
        if self.rmo.generation > self.rmo_last_generation:
            self.updated_object_types.add('RunningManipulators')
            self.rmo_last_generation = self.rmo.generation
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


if __name__ == '__main__':
    import manipulator_util_test
    manipulator_util_test.main()
