#!/usr/bin/env python

import logging

import manipulators
import screens
import task


class ScreenManager(object):

    def __init__(self, manipulator_manager):
        self._logger = logging.getLogger('kcaa.manipulator_util')
        self.objects = manipulator_manager.objects
        self.updated_object_types = manipulator_manager.updated_object_types
        self.click_queue = manipulator_manager.click_queue
        self.task_manager = manipulator_manager.task_manager
        self._last_screen_id = screens.UNKNOWN
        self._current_screen = manipulators.screen.Screen(self)
        self.define_screens()

    def define_screens(self):
        self.screens = {
            screens.PORT_MAIN: manipulators.screen.PortMainScreen,
            screens.SPECIAL_START: manipulators.screen.StartScreen,
        }

    def click(self, x, y):
        self.click_queue.put((x, y))

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
            else:
                self._logger.warn('Current screen {} is not manipulatable.'
                    .format(screen_id))
                self._current_screen = manipulators.screen.Screen(self)
        self._last_screen_id = screen_id


class ManipulatorManager(object):
    """Creates Kancolle manipulator, which assists user interaction by
    manipulating the Kancolle player (Flash) programatically."""

    def __init__(self, click_queue, objects, epoch):
        self.click_queue = click_queue
        self.objects = objects
        # TODO: Use Queue.Queue?
        self.queue = []
        self.task_manager = task.TaskManager(epoch)
        self.current_task = None
        self.define_manipulators()
        self.updated_object_types = set()
        self.screen_manager = ScreenManager(self)

    def define_manipulators(self):
        self.manipulators = {
            # Logistics
            'Charge': manipulators.logistics.Charge,
            # Special
            'StartGame': manipulators.special.StartGame,
        }

    def reload_manipulators(self):
        reload(manipulators)
        manipulators.reload_modules()
        self.define_manipulators()
        self.screen_manager = ScreenManager(self)

    def add_manipulator(self, manipulator):
        if self.task_manager.empty:
            self.current_task = manipulator
            self.task_manager.add(manipulator)
        else:
            self.queue.append(manipulator)

    def update(self, current):
        """Update manipulators.

        :param float current: Current time in seconds
        :returns: Updated KCSAPI objects
        :rtype: :class:`class:`kcaa.kcsapi.model.KCAAObject`
        """
        self.screen_manager.update_screen()
        self.task_manager.update(current)
        if self.task_manager.empty and self.queue:
            manipulator = self.queue[0]
            del self.queue[0]
            self.current_task = manipulator
            self.task_manager.add(manipulator)
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
