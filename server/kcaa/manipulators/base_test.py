#!/usr/bin/env python

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


def main():
    import doctest
    doctest.testmod(base)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
