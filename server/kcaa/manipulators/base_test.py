#!/usr/bin/env python

import pytest

import base
from kcaa import kcsapi


class MockManipulatorManager(object):

    def __init__(self):
        self.objects = {}
        self.screen_manager = None


class MockAutoManipulator(base.AutoManipulator):

    mockable_required_objects = []

    @classmethod
    def required_objects(cls):
        return cls.mockable_required_objects

    mockable_monitored_objects = []

    @classmethod
    def monitored_objects(cls):
        return cls.mockable_monitored_objects


class TestAutoManipulatorTriggerer(object):

    def pytest_funcarg__manipulator(self):
        return type('ClonedMockAutoManipulator', (MockAutoManipulator,),
                    {'mockable_monitored_objects': []})

    def test_has_required_objects_empty(self, manipulator):
        triggerer = base.AutoManipulatorTriggerer(
            MockManipulatorManager(), None, manipulator)
        assert triggerer.has_required_objects()

    def test_has_required_objects_single(self, manipulator):
        manipulator.mockable_required_objects = ['SomeObject']
        manager = MockManipulatorManager()
        triggerer = base.AutoManipulatorTriggerer(manager, None, manipulator)
        # The manipulator requires SomeObject; nothing is there, thus reject.
        assert not triggerer.has_required_objects()
        some_object = kcsapi.KCAAObject(generation=1)
        manager.objects['SomeObject'] = some_object
        # There is SomeObject with generation 1, it should accept that.
        assert triggerer.has_required_objects()

    def test_has_required_objects_double(self, manipulator):
        manipulator.mockable_required_objects = ['SomeObject', 'AnotherObject']
        manager = MockManipulatorManager()
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
            MockManipulatorManager(), None, manipulator)
        # If there is no monitored object, monitored objects are considered
        # ready.
        assert triggerer.get_object_generation_updates()[0]

    def test_get_object_generation_updates_single(self, manipulator):
        manipulator.mockable_monitored_objects = ['SomeObject']
        manager = MockManipulatorManager()
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
        manager = MockManipulatorManager()
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


def main():
    import doctest
    doctest.testmod(base)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
