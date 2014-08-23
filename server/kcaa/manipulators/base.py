#!/usr/bin/env python

import logging

from kcaa import task


logger = logging.getLogger('kcaa.manipulators.base')


class Manipulator(task.Task):

    def __init__(self, manager, *args, **kwargs):
        # Be sure to store required fields before calling super(), because
        # super() will call run() inside it.
        self.objects = manager.objects
        self.manager = manager
        self._screen_manager = manager.screen_manager
        super(Manipulator, self).__init__(*args, **kwargs)

    @property
    def screen(self):
        return self._screen_manager.current_screen

    @property
    def screen_id(self):
        return self.screen.screen_id

    def do_manipulator(self, manipulator, *args, **kwargs):
        return self.manager.task_manager.add(
            manipulator(self.manager, *args, **kwargs))

    def add_manipulator(self, manipulator, *args, **kwargs):
        return self.manager.add_manipulator(
            manipulator(self.manager, *args, **kwargs))


class AutoManipulatorTriggerer(Manipulator):

    def run(self, manipulator, interval=1.0, *args, **kwargs):
        self._manipulator = manipulator
        manipulator_name = manipulator.__name__
        while True:
            if self.manager.is_manipulator_scheduled(manipulator_name):
                yield interval
                continue
            params = manipulator.can_trigger(self, *args, **kwargs)
            if params is not None:
                logger.info('Triggering {}'.format(manipulator_name))
                self.add_manipulator(manipulator, **params)
            yield interval

    @property
    def manipulator(self):
        return self._manipulator


class AutoManipulator(Manipulator):

    @classmethod
    def can_trigger(cls, owner):
        return None
