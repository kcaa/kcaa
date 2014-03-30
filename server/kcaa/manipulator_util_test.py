#!/usr/bin/env python

import pytest

import manipulator_util


class TestManipulatorManager(object):

    def pytest_funcarg__manager(self, request):
        return manipulator_util.ManipulatorManager(None, {}, 0)

    def test_in_schedule_fragment(self):
        in_schedule_fragment = (
            manipulator_util.ManipulatorManager.in_schedule_fragment)
        assert in_schedule_fragment(0, [0, 3600])
        assert in_schedule_fragment(1800, [0, 3600])
        assert in_schedule_fragment(3599, [0, 3600])
        assert not in_schedule_fragment(3600, [0, 3600])
        assert not in_schedule_fragment(5400, [0, 3600])

    def test_are_auto_manipulator_scheduled_disabled(self, manager):
        manager.set_auto_manipulator_schedules(False, [[0, 3600]])
        assert not manager.are_auto_manipulator_scheduled(0)

    def test_are_auto_manipulator_scheduled_one_fragment(self, manager):
        manager.set_auto_manipulator_schedules(True, [[0, 3600]])
        assert manager.are_auto_manipulator_scheduled(0)
        assert manager.are_auto_manipulator_scheduled(1800)
        assert manager.are_auto_manipulator_scheduled(3599)
        assert not manager.are_auto_manipulator_scheduled(3600)
        assert not manager.are_auto_manipulator_scheduled(5400)

    def test_are_auto_manipulator_scheduled_two_fragments(self, manager):
        manager.set_auto_manipulator_schedules(True, [[0, 3600],
                                                      [7200, 10800]])
        assert manager.are_auto_manipulator_scheduled(0)
        assert not manager.are_auto_manipulator_scheduled(3600)
        assert manager.are_auto_manipulator_scheduled(7200)
        assert manager.are_auto_manipulator_scheduled(10799)
        assert not manager.are_auto_manipulator_scheduled(10800)
        assert manager.are_auto_manipulator_scheduled(0)

    def test_are_auto_manipulator_scheduled_two_overlapping_fragments(
            self, manager):
        manager.set_auto_manipulator_schedules(True, [[0, 3600],
                                                      [1800, 7200]])
        assert manager.are_auto_manipulator_scheduled(0)
        assert manager.are_auto_manipulator_scheduled(3600)
        assert manager.are_auto_manipulator_scheduled(7199)
        assert not manager.are_auto_manipulator_scheduled(7200)
        assert manager.are_auto_manipulator_scheduled(0)

    def test_are_auto_manipulator_scheduled_current_fragment_deleted(
            self, manager):
        manager.set_auto_manipulator_schedules(True, [[0, 3600]])
        assert manager.are_auto_manipulator_scheduled(0)
        manager.set_auto_manipulator_schedules(True, [])
        assert not manager.are_auto_manipulator_scheduled(0)


def main():
    import doctest
    doctest.testmod(manipulator_util)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
