#!/usr/bin/env python

import manipulators
import screens
import task


class ScreenManager(object):

    def __init__(self, manipulator_manager):
        self.click_queue = manipulator_manager.click_queue
        self.task_manager = manipulator_manager.task_manager
        self._current_screen = manipulators.base.Screen(self)

    def define_manipulators(self):
        self.manipulators = {
            screens.PORT_MAIN: manipulators.base.Screen,
        }

    def click(self, x, y):
        self.click_queue.put((x, y))

    def add_task(self, t):
        return self.task_manager.add(t)

    @property
    def current_screen(self):
        return self._current_screen


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
        self.screen_manager = ScreenManager(self)

    def define_manipulators(self):
        self.manipulators = {
            'Charge': manipulators.port.Charge,
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
        self.task_manager.update(current)
        if self.task_manager.empty and self.queue:
            manipulator = self.queue[0]
            del self.queue[0]
            self.current_task = manipulator
            self.task_manager.add(manipulator)

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
