#!/usr/bin/env python

import datetime

import pytest

import base
from kcaa import kcsapi
from kcaa import manipulator_util


class TestManipulator(object):

    def test_require_objects(object):
        class Manipulator(base.Manipulator):
            def run(self):
                self.require_objects(['ShipList', 'FleetList'])
                yield 0.0

        manager = manipulator_util.MockManipulatorManager()
        manipulator = Manipulator(manager, priority=0)
        with pytest.raises(Exception):
            manipulator.update(0.1)
        assert not manipulator.alive
        assert (manipulator.exception.message ==
                'Required object ShipList not found')
        manager.objects['ShipList'] = None
        manipulator = Manipulator(manager, priority=0)
        with pytest.raises(Exception):
            manipulator.update(0.1)
        assert not manipulator.alive
        assert (manipulator.exception.message ==
                'Required object FleetList not found')
        manager.objects['FleetList'] = None
        manipulator = Manipulator(manager, priority=0)
        with pytest.raises(StopIteration):
            manipulator.update(0.1)
        assert not manipulator.alive
        assert manipulator.success


class TestAutoManipulatorTriggerer(object):

    def pytest_funcarg__manipulator(self):
        return base.MockAutoManipulator.clone()

    def test_has_required_objects_empty(self, manipulator):
        triggerer = base.AutoManipulatorTriggerer(
            manipulator_util.MockManipulatorManager(), None, manipulator)
        assert triggerer.has_required_objects()

    def test_has_required_objects_single(self, manipulator):
        manipulator.mockable_required_objects = ['SomeObject']
        manager = manipulator_util.MockManipulatorManager()
        triggerer = base.AutoManipulatorTriggerer(manager, None, manipulator)
        # The manipulator requires SomeObject; nothing is there, thus reject.
        assert not triggerer.has_required_objects()
        some_object = kcsapi.KCAAObject(generation=1)
        manager.objects['SomeObject'] = some_object
        # There is SomeObject with generation 1, it should accept that.
        assert triggerer.has_required_objects()

    def test_has_required_objects_double(self, manipulator):
        manipulator.mockable_required_objects = ['SomeObject', 'AnotherObject']
        manager = manipulator_util.MockManipulatorManager()
        triggerer = base.AutoManipulatorTriggerer(manager, None, manipulator)
        # No object is available.
        assert not triggerer.has_required_objects()
        some_object = kcsapi.KCAAObject(generation=1)
        manager.objects['SomeObject'] = some_object
        # SomeObject is there, but AnotherObject is not; reject.
        assert not triggerer.has_required_objects()
        another_object = kcsapi.KCAAObject(generation=1)
        manager.objects['AnotherObject'] = another_object
        # Now both objects are present.
        assert triggerer.has_required_objects()

    def test_get_objeect_generation_updates_empty(self, manipulator):
        triggerer = base.AutoManipulatorTriggerer(
            manipulator_util.MockManipulatorManager(), None, manipulator)
        # If there is no monitored object, monitored objects are considered
        # ready.
        assert triggerer.get_object_generation_updates()[0]

    def test_get_object_generation_updates_single(self, manipulator):
        manipulator.mockable_monitored_objects = ['SomeObject']
        manager = manipulator_util.MockManipulatorManager()
        triggerer = base.AutoManipulatorTriggerer(manager, None, manipulator)
        # The manipulator requires SomeObject; nothing is there, thus reject.
        assert not triggerer.get_object_generation_updates()[0]
        some_object = kcsapi.KCAAObject(generation=1)
        manager.objects['SomeObject'] = some_object
        # There is SomeObject with generation 1, it should accept that.
        assert (triggerer.get_object_generation_updates() ==
                (True, True, {'SomeObject': 1}))
        triggerer.update_generations({'SomeObject': 1})
        # Now the update was consumed. Consecutive calls should reject.
        assert (triggerer.get_object_generation_updates() ==
                (True, False, {}))
        assert (triggerer.get_object_generation_updates() ==
                (True, False, {}))
        some_object.generation += 1
        # SomeObject was updated. The first call should accept.
        assert (triggerer.get_object_generation_updates() ==
                (True, True, {'SomeObject': 2}))
        triggerer.update_generations({'SomeObject': 2})
        assert (triggerer.get_object_generation_updates() ==
                (True, False, {}))

    def test_get_object_generation_updates_double(self, manipulator):
        manipulator.mockable_monitored_objects = ['SomeObject',
                                                  'AnotherObject']
        manager = manipulator_util.MockManipulatorManager()
        triggerer = base.AutoManipulatorTriggerer(manager, None, manipulator)
        # No object is available.
        assert not triggerer.get_object_generation_updates()[0]
        some_object = kcsapi.KCAAObject(generation=1)
        manager.objects['SomeObject'] = some_object
        # SomeObject is there, but AnotherObject is not; reject.
        assert not triggerer.get_object_generation_updates()[0]
        another_object = kcsapi.KCAAObject(generation=1)
        manager.objects['AnotherObject'] = another_object
        # Now both objects are present.
        assert (triggerer.get_object_generation_updates() ==
                (True, True, {'SomeObject': 1, 'AnotherObject': 1}))
        triggerer.update_generations({'SomeObject': 1, 'AnotherObject': 1})
        assert (triggerer.get_object_generation_updates() ==
                (True, False, {}))
        # Any updates in either object can be accepted.
        some_object.generation += 1
        assert (triggerer.get_object_generation_updates() ==
                (True, True, {'SomeObject': 2}))
        triggerer.update_generations({'SomeObject': 2})
        assert (triggerer.get_object_generation_updates() ==
                (True, False, {}))
        another_object.generation += 1
        assert (triggerer.get_object_generation_updates() ==
                (True, True, {'AnotherObject': 2}))
        triggerer.update_generations({'AnotherObject': 2})
        assert (triggerer.get_object_generation_updates() ==
                (True, False, {}))

    def test_run_already_scheduled(self, manipulator):
        manager = manipulator_util.MockManipulatorManager()
        triggerer = base.AutoManipulatorTriggerer(manager, None, manipulator)
        manager.scheduled_manipulators['MockAutoManipulator'] = manipulator
        assert not manipulator.can_trigger_called
        triggerer.update(0.1)
        assert not manipulator.can_trigger_called
        del manager.scheduled_manipulators['MockAutoManipulator']
        triggerer.update(0.2)
        assert manipulator.can_trigger_called

    def test_run_required_objects(self, manipulator):
        manipulator.mockable_required_objects = ['SomeObject']
        manager = manipulator_util.MockManipulatorManager()
        triggerer = base.AutoManipulatorTriggerer(manager, None, manipulator)
        assert not manipulator.can_trigger_called
        triggerer.update(0.1)
        assert not manipulator.can_trigger_called
        some_object = kcsapi.KCAAObject(generation=1)
        manager.objects['SomeObject'] = some_object
        triggerer.update(0.2)
        assert manipulator.can_trigger_called

    def test_run_monitored_objects(self, manipulator):
        manipulator.mockable_monitored_objects = ['SomeObject']
        manager = manipulator_util.MockManipulatorManager()
        triggerer = base.AutoManipulatorTriggerer(manager, None, manipulator)
        assert not manipulator.can_trigger_called
        triggerer.update(0.1)
        assert not manipulator.can_trigger_called
        some_object = kcsapi.KCAAObject(generation=0)
        manager.objects['SomeObject'] = some_object
        triggerer.update(0.2)
        assert not manipulator.can_trigger_called
        some_object.generation += 1
        triggerer.update(0.3)
        assert manipulator.can_trigger_called

    def test_run_run_only_when_idle(self, manipulator):
        manipulator.mockable_run_only_when_idle = True
        manager = manipulator_util.MockManipulatorManager()
        triggerer = base.AutoManipulatorTriggerer(manager, None, manipulator)
        manager.idle = False
        assert not manipulator.can_trigger_called
        triggerer.update(0.1)
        assert not manipulator.can_trigger_called
        manager.idle = True
        triggerer.update(0.2)
        assert manipulator.can_trigger_called

    def test_run_unaffected_by_idle(self, manipulator):
        manipulator.mockable_run_only_when_idle = False
        manager = manipulator_util.MockManipulatorManager()
        triggerer = base.AutoManipulatorTriggerer(manager, None, manipulator)
        manager.idle = False
        assert not manipulator.can_trigger_called
        triggerer.update(0.1)
        assert manipulator.can_trigger_called

    def test_run_precondition(self, manipulator):
        manipulator.mockable_precondition = False
        manager = manipulator_util.MockManipulatorManager()
        triggerer = base.AutoManipulatorTriggerer(manager, None, manipulator)
        assert not manipulator.can_trigger_called
        triggerer.update(0.1)
        assert not manipulator.can_trigger_called
        manipulator.mockable_precondition = True
        triggerer.update(0.2)
        assert manipulator.can_trigger_called

    # TODO: Add tests for screen generation check


class TestScheduledManipulator(object):

    def datetime(self, *args, **kwargs):
        return classmethod(lambda cls: datetime.datetime(*args, **kwargs))

    def pytest_funcarg__owner(self):
        return manipulator_util.MockManipulatorManager()

    def test_don_trigger_with_no_schedule(self, owner):
        class NoScheduleManipulator(base.ScheduledManipulator):
            run = lambda: None
        NoScheduleManipulator._now = self.datetime(2015, 1, 1, 0, 0)
        assert NoScheduleManipulator.can_trigger(owner) is None
        assert NoScheduleManipulator.can_trigger(owner) is None
        NoScheduleManipulator._now = self.datetime(2015, 1, 2, 0, 0)
        assert NoScheduleManipulator.can_trigger(owner) is None

    def test_dont_trigger_for_initial_run(self, owner):
        class SingleScheduleManipulator(base.ScheduledManipulator):
            schedules = classmethod(lambda cls: [datetime.time(9, 0)])
            run = lambda: None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 9, 1)
        assert SingleScheduleManipulator.can_trigger(owner) is None

    def test_trigger_for_first_schedule(self, owner):
        class SingleScheduleManipulator(base.ScheduledManipulator):
            schedules = classmethod(lambda cls: [datetime.time(9, 0)])
            run = lambda: None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 8, 58)
        assert SingleScheduleManipulator.can_trigger(owner) is None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 8, 59)
        assert SingleScheduleManipulator.can_trigger(owner) is None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 9, 0)
        assert SingleScheduleManipulator.can_trigger(owner) is not None

    def test_trigger_next_day(self, owner):
        class SingleScheduleManipulator(base.ScheduledManipulator):
            schedules = classmethod(lambda cls: [datetime.time(9, 0)])
            run = lambda: None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 9, 1)
        assert SingleScheduleManipulator.can_trigger(owner) is None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 2, 8, 59)
        assert SingleScheduleManipulator.can_trigger(owner) is None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 2, 9, 0)
        assert SingleScheduleManipulator.can_trigger(owner) is not None

    def test_trigger_two_schedules(self, owner):
        class DoubleScheduleManipulator(base.ScheduledManipulator):
            schedules = classmethod(lambda cls: [datetime.time(9, 0),
                                                 datetime.time(21, 0)])
            run = lambda: None
        DoubleScheduleManipulator._now = self.datetime(2015, 1, 1, 8, 59)
        assert DoubleScheduleManipulator.can_trigger(owner) is None
        DoubleScheduleManipulator._now = self.datetime(2015, 1, 1, 9, 0)
        assert DoubleScheduleManipulator.can_trigger(owner) is not None
        DoubleScheduleManipulator._now = self.datetime(2015, 1, 1, 9, 1)
        assert DoubleScheduleManipulator.can_trigger(owner) is None
        DoubleScheduleManipulator._now = self.datetime(2015, 1, 1, 20, 59)
        assert DoubleScheduleManipulator.can_trigger(owner) is None
        DoubleScheduleManipulator._now = self.datetime(2015, 1, 1, 21, 0)
        assert DoubleScheduleManipulator.can_trigger(owner) is not None
        DoubleScheduleManipulator._now = self.datetime(2015, 1, 1, 21, 1)
        assert DoubleScheduleManipulator.can_trigger(owner) is None
        DoubleScheduleManipulator._now = self.datetime(2015, 1, 2, 8, 59)
        assert DoubleScheduleManipulator.can_trigger(owner) is None
        DoubleScheduleManipulator._now = self.datetime(2015, 1, 2, 9, 0)
        assert DoubleScheduleManipulator.can_trigger(owner) is not None

    def test_trigger_within_acceptable_range(self, owner):
        class SingleScheduleManipulator(base.ScheduledManipulator):
            schedules = classmethod(lambda cls: [datetime.time(9, 0)])
            acceptable_delay = classmethod(
                lambda cls: datetime.timedelta(hours=1))
            run = lambda: None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 8, 59)
        assert SingleScheduleManipulator.can_trigger(owner) is None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 9, 59)
        assert SingleScheduleManipulator.can_trigger(owner) is not None

    def test_dont_trigger_exceeding_acceptable_range(self, owner):
        class SingleScheduleManipulator(base.ScheduledManipulator):
            schedules = classmethod(lambda cls: [datetime.time(9, 0)])
            acceptable_delay = classmethod(
                lambda cls: datetime.timedelta(hours=1))
            run = lambda: None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 8, 59)
        assert SingleScheduleManipulator.can_trigger(owner) is None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 10, 0)
        assert SingleScheduleManipulator.can_trigger(owner) is None
        # Try for the next schedule.
        SingleScheduleManipulator._now = self.datetime(2015, 1, 2, 8, 59)
        assert SingleScheduleManipulator.can_trigger(owner) is None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 2, 9, 0)
        assert SingleScheduleManipulator.can_trigger(owner) is not None

    def test_trigger_random_delay(self, owner):
        class SingleScheduleManipulator(base.ScheduledManipulator):
            schedules = classmethod(lambda cls: [datetime.time(9, 0)])
            random_delay_params = classmethod(
                lambda cls: base.GammaDistributedRandomDelayParams(
                    1.0, 2.0, 60))
            run = lambda: None

        class MockRandom(object):
            def gammavariate(self, alpha, beta):
                assert alpha == 1.0
                assert beta == 2.0
                return 3

        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 8, 59, 0)
        SingleScheduleManipulator._rand = MockRandom()
        assert SingleScheduleManipulator.can_trigger(owner) is None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 9, 0, 0)
        assert SingleScheduleManipulator.can_trigger(owner) is None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 9, 0, 2)
        assert SingleScheduleManipulator.can_trigger(owner) is None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 9, 0, 3)
        assert SingleScheduleManipulator.can_trigger(owner) is not None

    def test_trigger_random_delay_max_delay_capped(self, owner):
        class SingleScheduleManipulator(base.ScheduledManipulator):
            schedules = classmethod(lambda cls: [datetime.time(9, 0)])
            random_delay_params = classmethod(
                lambda cls: base.GammaDistributedRandomDelayParams(
                    10.0, 20.0, 60))
            run = lambda: None

        class MockRandom(object):
            def gammavariate(self, alpha, beta):
                assert alpha == 10.0
                assert beta == 20.0
                return 200

        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 8, 59, 0)
        SingleScheduleManipulator._rand = MockRandom()
        assert SingleScheduleManipulator.can_trigger(owner) is None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 9, 0, 0)
        assert SingleScheduleManipulator.can_trigger(owner) is None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 9, 0, 59)
        assert SingleScheduleManipulator.can_trigger(owner) is None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 9, 1, 0)
        assert SingleScheduleManipulator.can_trigger(owner) is not None

    def test_trigger_random_delay_but_within_acceptable_range(self, owner):
        class SingleScheduleManipulator(base.ScheduledManipulator):
            schedules = classmethod(lambda cls: [datetime.time(9, 0)])
            acceptable_delay = classmethod(
                lambda cls: datetime.timedelta(seconds=60))
            random_delay_params = classmethod(
                lambda cls: base.GammaDistributedRandomDelayParams(
                    10.0, 20.0, 120))
            run = lambda: None

        class MockRandom(object):
            def gammavariate(self, alpha, beta):
                return 59

        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 8, 59, 0)
        SingleScheduleManipulator._rand = MockRandom()
        assert SingleScheduleManipulator.can_trigger(owner) is None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 9, 0, 0)
        assert SingleScheduleManipulator.can_trigger(owner) is None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 9, 0, 59)
        assert SingleScheduleManipulator.can_trigger(owner) is not None

    def test_dont_trigger_random_delay_exceeding_acceptable_range(self, owner):
        class SingleScheduleManipulator(base.ScheduledManipulator):
            schedules = classmethod(lambda cls: [datetime.time(9, 0)])
            acceptable_delay = classmethod(
                lambda cls: datetime.timedelta(seconds=60))
            random_delay_params = classmethod(
                lambda cls: base.GammaDistributedRandomDelayParams(
                    10.0, 20.0, 120))
            run = lambda: None

        class MockRandom(object):
            def gammavariate(self, alpha, beta):
                return 60

        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 8, 59, 0)
        SingleScheduleManipulator._rand = MockRandom()
        assert SingleScheduleManipulator.can_trigger(owner) is None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 9, 0, 0)
        assert SingleScheduleManipulator.can_trigger(owner) is None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 9, 0, 59)
        assert SingleScheduleManipulator.can_trigger(owner) is None
        SingleScheduleManipulator._now = self.datetime(2015, 1, 1, 9, 1, 0)
        assert SingleScheduleManipulator.can_trigger(owner) is None

    def test_trigger_for_wanted_object(self, owner):
        class WantingScheduleManipulator(base.ScheduledManipulator):
            schedules = classmethod(lambda cls: [datetime.time(9, 0)])
            wanted_objects = classmethod(lambda cls: ['Foo', 'Bar'])
            run = lambda: None
        WantingScheduleManipulator._now = self.datetime(2015, 1, 1, 0, 0)
        assert WantingScheduleManipulator.can_trigger(owner) is not None

    def test_trigger_for_partially_wanted_object(self, owner):
        class WantingScheduleManipulator(base.ScheduledManipulator):
            schedules = classmethod(lambda cls: [datetime.time(9, 0)])
            wanted_objects = classmethod(lambda cls: ['Foo', 'Bar'])
            run = lambda: None
        WantingScheduleManipulator._now = self.datetime(2015, 1, 1, 0, 0)
        owner.objects = {'Foo': None}
        # Bar is still missing.
        assert WantingScheduleManipulator.can_trigger(owner) is not None

    def test_dont_trigger_for_satisfied_wanted_object(self, owner):
        class WantingScheduleManipulator(base.ScheduledManipulator):
            schedules = classmethod(lambda cls: [datetime.time(9, 0)])
            wanted_objects = classmethod(lambda cls: ['Foo', 'Bar'])
            run = lambda: None
        WantingScheduleManipulator._now = self.datetime(2015, 1, 1, 0, 0)
        owner.objects = {'Foo': None, 'Bar': None}
        assert WantingScheduleManipulator.can_trigger(owner) is None


def main():
    import doctest
    doctest.testmod(base)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
