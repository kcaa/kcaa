#!/usr/bin/env python

import logging

from kcaa import task


logger = logging.getLogger('kcaa.manipulators.base')


class Manipulator(task.Task):

    def __init__(self, manager, priority, *args, **kwargs):
        # Be sure to store required fields before calling super(), because
        # super() will call run() inside it.
        self.objects = manager.objects
        self.manager = manager
        self.priority = priority
        self._screen_manager = manager.screen_manager
        super(Manipulator, self).__init__(*args, **kwargs)

    @property
    def screen(self):
        return self._screen_manager.current_screen

    @property
    def screen_id(self):
        return self.screen.screen_id

    def do_manipulator(self, manipulator, *args, **kwargs):
        """Run a manipulator immediately.

        :param manipulator: manipulator class object
        :param args: positional arguments to manipulator constructor (optional)
        :param kwargs: keyword arguments to manipulator constructor (optional)
        :returns: task object

        Run the manipulator immediately. This means other manipulators and auto
        "manipulators will have no chance to interrupt even if it has a higher
        priority.

        Typically the caller will block itself by yielding the return value.
        """
        logger.debug('Manipulator.do_manipulator({}, *{}, **{})'.format(
            manipulator.__name__, args, kwargs))
        return self.manager.task_manager.add(
            manipulator(self.manager, 0, *args, **kwargs))

    def add_manipulator(self, manipulator, *args, **kwargs):
        """Schedule a manipulator.

        :param manipulator: manipulator class object
        :param args: positional arguments to manipulator constructor (optional)
        :param kwargs: keyword arguments to manipulator constructor (optional)
        :returns: task object

        Schedule the manipulator to be run later. This means other manipulators
        and auto manipulators can interrupt if it has a higher priority. The
        scheduled manipulator will run with a priority 1 less than the priority
        of this manipulator, which makes it scheduled earlier than the sibling
        manipulators of this.

        Typically the caller will not block itself.
        """
        return self.add_manipulator_priority(
            manipulator, self.priority - 1, *args, **kwargs)

    def add_manipulator_priority(self, manipulator, priority, *args, **kwargs):
        logger.debug(
            'Manipulator.add_manipulator_priority({}, priority={}, *{}, **{})'
            .format(manipulator.__name__, priority, args, kwargs))
        return self.manager.add_manipulator(
            manipulator(self.manager, priority, *args, **kwargs))


class AutoManipulatorTriggerer(Manipulator):

    def run(self, manipulator, interval=-1, *args, **kwargs):
        self._manipulator = manipulator
        manipulator_name = manipulator.__name__
        while True:
            if self.manager.is_manipulator_scheduled(manipulator_name):
                yield interval
                continue
            params = manipulator.can_trigger(self, *args, **kwargs)
            if params is not None:
                logger.info('Triggering {}'.format(manipulator_name))
                self.add_manipulator_priority(manipulator, None, **params)
            yield interval

    @property
    def manipulator(self):
        return self._manipulator


class AutoManipulator(Manipulator):

    @classmethod
    def can_trigger(cls, owner):
        return None
