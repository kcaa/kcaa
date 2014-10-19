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


class TestAutoManipulatorTriggerer(object):

    def pytest_funcarg__manipulator(self):
        return type('ClonedMockAutoManipulator', (MockAutoManipulator,),
                    {'mockable_required_objects': []})

    def test_update_object_generation_empty(self, manipulator):
        print MockAutoManipulator.required_objects()
        triggerer = base.AutoManipulatorTriggerer(
            MockManipulatorManager(), None, manipulator)
        # If there is no required object, always accept updates.
        assert triggerer.update_object_generation()
        assert triggerer.update_object_generation()

    def test_update_object_generation_single(self, manipulator):
        manipulator.mockable_required_objects = ['SomeObject']
        manager = MockManipulatorManager()
        triggerer = base.AutoManipulatorTriggerer(manager, None, manipulator)
        # The manipulator requires SomeObject; nothing is there, thus reject.
        assert not triggerer.update_object_generation()
        some_object = kcsapi.KCAAObject(generation=1)
        manager.objects['SomeObject'] = some_object
        # There is SomeObject with generation 1, it should accept that.
        assert triggerer.update_object_generation()
        # Now the update was consumed. Consecutive calls should reject.
        assert not triggerer.update_object_generation()
        assert not triggerer.update_object_generation()
        some_object.generation += 1
        # SomeObject was updated. The first call should accept.
        assert triggerer.update_object_generation()
        assert not triggerer.update_object_generation()

    def test_update_object_generation_double(self, manipulator):
        manipulator.mockable_required_objects = ['SomeObject', 'AnotherObject']
        manager = MockManipulatorManager()
        triggerer = base.AutoManipulatorTriggerer(manager, None, manipulator)
        # No object is available.
        assert not triggerer.update_object_generation()
        some_object = kcsapi.KCAAObject(generation=1)
        manager.objects['SomeObject'] = some_object
        # SomeObject is there, but AnotherObject is not; reject.
        assert not triggerer.update_object_generation()
        another_object = kcsapi.KCAAObject(generation=1)
        manager.objects['AnotherObject'] = another_object
        # Now both objects are present.
        assert triggerer.update_object_generation()
        assert not triggerer.update_object_generation()
        # Any updates in either object can be accepted.
        some_object.generation += 1
        assert triggerer.update_object_generation()
        assert not triggerer.update_object_generation()
        another_object.generation += 1
        assert triggerer.update_object_generation()
        assert not triggerer.update_object_generation()


def main():
    import doctest
    doctest.testmod(base)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
