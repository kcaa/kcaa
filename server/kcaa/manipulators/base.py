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
            manipulator(self.manager, self.priority - 1, *args, **kwargs))

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
        priority = 0 if self.priority > 0 else self.priority
        return self.add_manipulator_priority(
            manipulator, priority - 1, *args, **kwargs)

    def add_manipulator_priority(self, manipulator, priority, *args, **kwargs):
        logger.debug(
            'Manipulator.add_manipulator_priority({}, priority={}, *{}, **{})'
            .format(manipulator.__name__, priority, args, kwargs))
        return self.manager.add_manipulator(
            manipulator(self.manager, priority, *args, **kwargs))

    def require_objects(self, object_names):
        """Declare the objects are required to run, and fail if any of them is
        not available."""
        for object_name in object_names:
            if object_name not in self.objects:
                raise Exception('Required object {} not found'.format(
                    object_name))


class AutoManipulatorTriggerer(Manipulator):

    def __init__(self, manager, priority, manipulator, interval=-1,
                 check_interval=0, *args, **kwargs):
        super(AutoManipulatorTriggerer, self).__init__(manager, priority,
                                                       *args, **kwargs)
        self._manipulator = manipulator
        self._interval = interval
        self._check_interval = check_interval
        self._last_screen_generation = 0
        self._last_generations = (
            {obj_name: 0 for obj_name in manipulator.monitored_objects()})
        self._last_check_time = 0.0

    def run(self, *args, **kwargs):
        manipulator_name = self.manipulator.__name__
        self._last_check_time = self.epoch
        while True:
            screen_generation = self.screen.screen_generation
            has_monitored_objects, has_updates, updates = (
                self.get_object_generation_updates())
            # TODO: Test the screen generation check
            if (self.manager.is_manipulator_scheduled(manipulator_name) or
                    not self.has_required_objects() or
                    not has_monitored_objects or
                    not has_updates or
                    (self.manipulator.run_only_when_idle() and
                     not self.manager.idle) or
                    not self.manipulator.precondition(self) or
                    (screen_generation <= self._last_screen_generation and
                     self.time <=
                     self._last_check_time + self._check_interval)):
                yield self._interval
                continue
            self._last_screen_generation = self.screen.screen_generation
            self._last_check_time = self.time
            if has_updates:
                self.update_generations(updates)
            params = self.manipulator.can_trigger(self, *args, **kwargs)
            if params is not None:
                logger.info('Triggering {}'.format(manipulator_name))
                self.add_manipulator_priority(self.manipulator, None, **params)
            yield self._interval

    @property
    def manipulator(self):
        return self._manipulator

    def has_required_objects(self):
        return all(req_obj_name in self.objects for req_obj_name in
                   self.manipulator.required_objects())

    def get_object_generation_updates(self):
        if not self.manipulator.monitored_objects():
            return True, True, {}
        generation_updates = {}
        updated = False
        for req_obj_name in self.manipulator.monitored_objects():
            obj = self.objects.get(req_obj_name)
            if obj is None:
                return False, False, {}
            if obj.generation > self._last_generations[req_obj_name]:
                generation_updates[req_obj_name] = obj.generation
                updated = True
        return True, updated, generation_updates

    def update_generations(self, updates):
        self._last_generations.update(updates)


class AutoManipulator(Manipulator):

    @classmethod
    def required_objects(cls):
        """Required object names.

        Required objects are necessary for this auto manipulator to run, even
        for can_trigger().
        """
        return []

    @classmethod
    def monitored_objects(cls):
        """Monitored object names.

        Monitored objects are required objects whose updates are monitored.
        This auto manipulator won't run unless any of them is not updated.
        """
        return []

    @classmethod
    def run_only_when_idle(cls):
        """Whether to run only when the manipulator manager is idle."""
        return False

    @classmethod
    def precondition(cls, owner):
        """Generic precondition to run :meth:`can_trigger`.

        If suitable, prefer :meth:`required_objects`, :meth:`monitored_objects`
        or :meth:`run_only_when_idle` over this for readability.
        """
        return True

    @classmethod
    def can_trigger(cls, owner):
        return None


class MockAutoManipulator(AutoManipulator):
    """Mockable AutoManipulator.

    Always use :meth:`clone` so that mockable fields are local to the specific
    test case.
    """

    mockable_required_objects = []

    @classmethod
    def required_objects(cls):
        return cls.mockable_required_objects

    mockable_monitored_objects = []

    @classmethod
    def monitored_objects(cls):
        return cls.mockable_monitored_objects

    mockable_run_only_when_idle = False

    @classmethod
    def run_only_when_idle(cls):
        return cls.mockable_run_only_when_idle

    mockable_precondition = True

    @classmethod
    def precondition(cls, owner):
        return cls.mockable_precondition

    mockable_can_trigger = True
    can_trigger_called = False

    @classmethod
    def can_trigger(cls, owner):
        logger.debug('MockAutoManipulator.can_trigger: {}'.format(
            cls.mockable_can_trigger))
        cls.can_trigger_called = True
        return {} if cls.mockable_can_trigger else None

    run_called = False

    def run(self):
        logger.debug('MockAutoManipulator.run called.')
        self.run_called = True
        yield 0.0

    @staticmethod
    def clone(name='MockAutoManipulator'):
        return type(name, (MockAutoManipulator,),
                    {'mockable_required_objects': [],
                     'mockable_monitored_objects': [],
                     'mocakable_run_only_when_idle': False,
                     'mockable_precondition': True,
                     'mockable_can_trigger': True,
                     'can_trigger_called': False})
