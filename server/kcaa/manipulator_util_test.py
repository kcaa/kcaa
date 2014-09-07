#!/usr/bin/env python

import pytest

import kcsapi
import manipulator_util
import manipulators
import screens


SF = kcsapi.prefs.ScheduleFragment


class MockConnection(object):

    def send(self, value):
        pass


class MockManipulator(manipulators.base.Manipulator):

    def run(self, arg):
        yield self.unit


class TestScreenManager(object):

    def pytest_funcarg__manager(self, request):
        objects = {
            'Screen': kcsapi.client.Screen(),
        }
        manipulator_manager = manipulator_util.ManipulatorManager(
            MockConnection(), objects, kcsapi.prefs.Preferences(), 0)
        return manipulator_util.ScreenManager(manipulator_manager)

    def test_current_screen_id(self, manager):
        manager.objects['Screen'].screen = screens.PORT_MAIN
        assert manager.current_screen.screen_id == screens.PORT_MAIN
        manager.objects['Screen'].screen = screens.PORT_MISSION
        assert manager.current_screen.screen_id == screens.PORT_MISSION

    def test_update_screen_from_object(self, manager):
        manager.objects['Screen'].screen = screens.PORT_MAIN
        manager.update_screen()
        assert isinstance(manager.current_screen,
                          manipulators.screen.PortMainScreen)
        manager.objects['Screen'].screen = screens.PORT_MISSION
        manager.update_screen()
        assert isinstance(manager.current_screen,
                          manipulators.screen.PortMissionScreen)

    def test_update_screen_explicit(self, manager):
        manager.update_screen(screens.PORT_ORGANIZING)
        assert isinstance(manager.current_screen,
                          manipulators.screen.PortOrganizingScreen)
        assert manager.objects['Screen'].screen == screens.PORT_ORGANIZING
        manager.update_screen(screens.PORT_LOGISTICS)
        assert isinstance(manager.current_screen,
                          manipulators.screen.PortLogisticsScreen)
        assert manager.objects['Screen'].screen == screens.PORT_LOGISTICS


class TestManipulatorManager(object):

    def pytest_funcarg__manager(self, request):
        objects = {
            'RunningManipulators': kcsapi.client.RunningManipulators()
        }
        manager = manipulator_util.ManipulatorManager(
            MockConnection(), objects, kcsapi.prefs.Preferences(), 0)
        manager.manipulators = {
            'MockManipulator': MockManipulator,
        }
        return manager

    def test_in_schedule_fragment(self):
        in_schedule_fragment = (
            manipulator_util.ManipulatorManager.in_schedule_fragment)
        assert in_schedule_fragment(0, SF(start=0, end=3600))
        assert in_schedule_fragment(1800, SF(start=0, end=3600))
        assert in_schedule_fragment(3599, SF(start=0, end=3600))
        assert not in_schedule_fragment(3600, SF(start=0, end=3600))
        assert not in_schedule_fragment(5400, SF(start=0, end=3600))

    def test_are_auto_manipulator_scheduled_disabled(self, manager):
        manager.set_auto_manipulator_preferences(
            kcsapi.prefs.AutoManipulatorPreferences(
                enabled=False,
                schedules=[SF(start=0, end=3600)]))
        assert not manager.are_auto_manipulator_scheduled(0)

    def test_are_auto_manipulator_scheduled_one_fragment(self, manager):
        manager.set_auto_manipulator_preferences(
            kcsapi.prefs.AutoManipulatorPreferences(
                enabled=True,
                schedules=[SF(start=0, end=3600)]))
        assert manager.are_auto_manipulator_scheduled(0)
        assert manager.are_auto_manipulator_scheduled(1800)
        assert manager.are_auto_manipulator_scheduled(3599)
        assert not manager.are_auto_manipulator_scheduled(3600)
        assert not manager.are_auto_manipulator_scheduled(5400)

    def test_are_auto_manipulator_scheduled_two_fragments(self, manager):
        manager.set_auto_manipulator_preferences(
            kcsapi.prefs.AutoManipulatorPreferences(
                enabled=True,
                schedules=[SF(start=0, end=3600),
                           SF(start=7200, end=10800)]))
        assert manager.are_auto_manipulator_scheduled(0)
        assert not manager.are_auto_manipulator_scheduled(3600)
        assert manager.are_auto_manipulator_scheduled(7200)
        assert manager.are_auto_manipulator_scheduled(10799)
        assert not manager.are_auto_manipulator_scheduled(10800)
        assert manager.are_auto_manipulator_scheduled(0)

    def test_are_auto_manipulator_scheduled_two_overlapping_fragments(
            self, manager):
        manager.set_auto_manipulator_preferences(
            kcsapi.prefs.AutoManipulatorPreferences(
                enabled=True,
                schedules=[SF(start=0, end=3600),
                           SF(start=1800, end=7200)]))
        assert manager.are_auto_manipulator_scheduled(0)
        assert manager.are_auto_manipulator_scheduled(3600)
        assert manager.are_auto_manipulator_scheduled(7199)
        assert not manager.are_auto_manipulator_scheduled(7200)
        assert manager.are_auto_manipulator_scheduled(0)

    def test_are_auto_manipulator_scheduled_current_fragment_deleted(
            self, manager):
        manager.set_auto_manipulator_preferences(
            kcsapi.prefs.AutoManipulatorPreferences(
                enabled=True,
                schedules=[SF(start=0, end=3600)]))
        assert manager.are_auto_manipulator_scheduled(0)
        manager.set_auto_manipulator_preferences(
            kcsapi.prefs.AutoManipulatorPreferences(
                enabled=True,
                schedules=[]))
        assert not manager.are_auto_manipulator_scheduled(0)

    def test_add_manipulator_preserve_order(self, manager):
        assert not manager.queue
        M1 = type('MockManipulator1', (MockManipulator,), {})
        m1 = M1(manager, 0, arg='value')
        manager.add_manipulator(m1)
        assert manager.queue == [(0, 0, m1)]
        M2 = type('MockManipulator2', (MockManipulator,), {})
        m2 = M2(manager, 0, arg='value')
        manager.add_manipulator(m2)
        assert manager.queue == [(0, 0, m1), (0, 1, m2)]

    def test_add_manipulator_prefer_higher_priority_task(self, manager):
        assert not manager.queue
        M1 = type('MockManipulator1', (MockManipulator,), {})
        m1 = M1(manager, 0, arg='value')
        manager.add_manipulator(m1)
        assert manager.queue == [(0, 0, m1)]
        M2 = type('MockManipulator2', (MockManipulator,), {})
        m2 = M2(manager, -100, arg='value')
        manager.add_manipulator(m2)
        assert manager.queue == [(-100, 1, m2), (0, 0, m1)]

    def test_dispatch_invalid_fomat(self, manager):
        with pytest.raises(ValueError):
            manager.dispatch(('Manipulator',))
        with pytest.raises(ValueError):
            manager.dispatch(('Manipulator', {'arg': 'value'}, 'something'))

    def test_dispatch_unknown_command(self, manager):
        with pytest.raises(ValueError):
            manager.dispatch(('NonExistentManipulator', {'arg', 'value'}))

    def test_dispatch_argument_mismatch(self, manager):
        with pytest.raises(TypeError):
            manager.dispatch(('MockManipulator', {}))
        with pytest.raises(TypeError):
            manager.dispatch(('MockManipulator',
                             {'non_existent_arg': 'value'}))

    def test_dispatch_charge_fleet(self, manager):
        assert manager.manipulator_queue == []
        manager.dispatch(('MockManipulator', {'arg': 'value'}))
        manipulator_queue = manager.manipulator_queue
        assert len(manipulator_queue) == 1
        # Manipulator object is stored as the 3rd element.
        assert isinstance(manipulator_queue[0][2], MockManipulator)


def main():
    import doctest
    doctest.testmod(manipulator_util)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
