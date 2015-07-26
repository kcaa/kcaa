#!/usr/bin/env python

import pytest

import kcsapi
import logenv
import manipulator_util
import manipulators
import screens

SF = kcsapi.prefs.ScheduleFragment

logger = logenv.setup_logger_for_test()


class MockQueue(object):

    def put(self, value):
        pass


class MockManipulator(manipulators.base.Manipulator):
    arg = 'arg_default'

    def run(self, arg):
        self.arg = arg
        yield self.unit


class TestScreenManager(object):

    def pytest_funcarg__manager(self, request):
        objects = {
            'Screen': kcsapi.client.Screen(),
        }
        states = {}
        manipulator_manager = manipulator_util.ManipulatorManager(
            MockQueue(), objects, states, kcsapi.prefs.Preferences(), 0)
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
        states = {}
        manager = manipulator_util.ManipulatorManager(
            MockQueue(), objects, states, kcsapi.prefs.Preferences(), 0)
        manager.manipulators = {
            'MockManipulator': MockManipulator,
        }
        # Clear default auto manipulators.
        # TODO: Inject auto manipulators more cleanly.
        manager.auto_manipulators = {}
        for triggerer in manager.running_auto_triggerer:
            manager.task_manager.remove(triggerer)
        del manager.running_auto_triggerer[:]
        self.enable_auto_manipulators(manager, enabled=False)
        return manager

    def enable_auto_manipulators(self, manager, enabled=True):
        manager.set_auto_manipulator_preferences(
            kcsapi.prefs.AutoManipulatorPreferences(
                enabled=enabled,
                schedules=[SF(start=0, end=86400)]))

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
        assert not manager.is_manipulator_scheduled('MockManipulator1')
        M1 = type('MockManipulator1', (MockManipulator,), {})
        m1 = M1(manager, 0, arg='value')
        manager.add_manipulator(m1)
        assert manager.queue == [(0, 0, m1)]
        assert manager.is_manipulator_scheduled('MockManipulator1')
        assert not manager.is_manipulator_scheduled('MockManipulator2')
        M2 = type('MockManipulator2', (MockManipulator,), {})
        m2 = M2(manager, 0, arg='value')
        manager.add_manipulator(m2)
        assert manager.queue == [(0, 0, m1), (0, 1, m2)]
        assert manager.is_manipulator_scheduled('MockManipulator2')

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

    def test_is_manipulator_scheduled_multiple_entries(self, manager):
        assert not manager.is_manipulator_scheduled('MockManipulator')
        m1 = MockManipulator(manager, 0, arg='value1')
        manager.add_manipulator(m1)
        assert manager.is_manipulator_scheduled('MockManipulator')
        m2 = MockManipulator(manager, 0, arg='value2')
        manager.add_manipulator(m2)
        assert manager.is_manipulator_scheduled('MockManipulator')
        manager.update(0.1)
        assert manager.current_task is m1
        assert manager.is_manipulator_scheduled('MockManipulator')
        manager.update(0.2)
        assert manager.current_task is m1
        assert manager.is_manipulator_scheduled('MockManipulator')
        manager.update(0.3)
        assert manager.current_task is None
        assert manager.last_task is m1
        assert manager.is_manipulator_scheduled('MockManipulator')
        manager.update(0.4)
        assert manager.current_task is m2
        assert manager.is_manipulator_scheduled('MockManipulator')
        manager.update(0.5)
        assert manager.current_task is m2
        assert manager.is_manipulator_scheduled('MockManipulator')
        manager.update(0.6)
        assert manager.current_task is None
        assert manager.last_task is m2
        assert not manager.is_manipulator_scheduled('MockManipulator')

    def test_is_manipulator_scheduled_multiple_entries_recursively(
            self, manager):
        assert not manager.is_manipulator_scheduled('MockManipulator')
        m1 = MockManipulator(manager, 0, arg='value1')
        manager.add_manipulator(m1)
        assert manager.is_manipulator_scheduled('MockManipulator')
        # Unlike the 'multiple_entries' case, the first manipulator begins to
        # run at this moment. This is more realistic configuration when a
        # manipulator recursively invoke itself.
        # Note that m1 will have been popped from the queue.
        manager.update(0.1)
        assert manager.current_task is m1
        assert manager.is_manipulator_scheduled('MockManipulator')
        # Assume m2 is the manipulator added by m1 with a recursive call.
        # Thus it has smaller priority than m1.
        m2 = MockManipulator(manager, -1, arg='value2')
        manager.add_manipulator(m2)
        assert manager.is_manipulator_scheduled('MockManipulator')
        manager.update(0.2)
        assert manager.current_task is m1
        assert manager.is_manipulator_scheduled('MockManipulator')
        manager.update(0.3)
        # Now, m1 finished.
        # However 'MockManipulator' is still considered scheduled because m2 is
        # waiting to run.
        assert manager.current_task is None
        assert manager.last_task is m1
        assert manager.is_manipulator_scheduled('MockManipulator')
        manager.update(0.4)
        assert manager.current_task is m2
        assert manager.is_manipulator_scheduled('MockManipulator')
        manager.update(0.5)
        assert manager.current_task is m2
        assert manager.is_manipulator_scheduled('MockManipulator')
        manager.update(0.6)
        assert manager.current_task is None
        assert manager.last_task is m2
        assert not manager.is_manipulator_scheduled('MockManipulator')

    def test_is_manipulator_scheduled_higher_priority_finish_earlier(
            self, manager):
        assert not manager.is_manipulator_scheduled('MockManipulator')
        m1 = MockManipulator(manager, 0, arg='value1')
        manager.add_manipulator(m1)
        assert manager.is_manipulator_scheduled('MockManipulator')
        m2 = MockManipulator(manager, -1, arg='value2')
        manager.add_manipulator(m2)
        assert manager.is_manipulator_scheduled('MockManipulator')
        manager.update(0.1)
        assert manager.current_task is m2
        assert manager.is_manipulator_scheduled('MockManipulator')
        manager.update(0.2)
        assert manager.current_task is m2
        assert manager.is_manipulator_scheduled('MockManipulator')
        manager.update(0.3)
        assert manager.current_task is None
        assert manager.last_task is m2
        assert manager.is_manipulator_scheduled('MockManipulator')
        manager.update(0.4)
        assert manager.current_task is m1
        assert manager.is_manipulator_scheduled('MockManipulator')
        manager.update(0.5)
        assert manager.current_task is m1
        assert manager.is_manipulator_scheduled('MockManipulator')
        manager.update(0.6)
        assert manager.current_task is None
        assert manager.last_task is m1
        assert not manager.is_manipulator_scheduled('MockManipulator')

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

    def test_start_task_from_queue_empty(self, manager):
        assert manager.current_task is None
        assert manager.last_task is None
        assert not manager.queue
        manager.start_task_from_queue()
        assert manager.current_task is None
        assert manager.last_task is None

    def test_start_task_from_queue_start_running(self, manager):
        m = manager.add_manipulator(MockManipulator(manager, 0, arg='value'))
        assert not m.running
        manager.start_task_from_queue()
        assert manager.current_task is m
        assert manager.last_task is None
        assert m.running

    def test_finish_current_task(self, manager):
        assert manager.current_task is None
        assert manager.last_task is None
        assert not manager.is_manipulator_scheduled('MockManipulator')
        m = manager.add_manipulator(MockManipulator(manager, 0, arg='value'))
        assert manager.is_manipulator_scheduled('MockManipulator')
        manager.start_task_from_queue()
        # MockManipulator should end running after 1 unit time.
        manager.task_manager.update(0.1)
        manager.task_manager.update(0.2)
        assert manager.current_task is m
        assert manager.current_task not in manager.task_manager.tasks
        manager.finish_current_task()
        assert manager.current_task is None
        assert manager.last_task is m
        assert not manager.is_manipulator_scheduled('MockManipulator')

    def test_update_normal(self, manager):
        m = MockManipulator(manager, 0, arg='value')
        manager.add_manipulator(m)
        assert m.arg == 'arg_default'
        manager.update(0.1)
        assert m.arg == 'value'

    def test_update_prefer_higher_priority_auto_manipulator(self, manager):
        class AutoMockManipulatorA(manipulators.base.AutoManipulator):
            started = False
            done = False

            @classmethod
            def can_trigger(cls, owner):
                return {}

            def run(self):
                self.started = True
                yield self.unit
                self.done = True

        class AutoMockManipulatorB(manipulators.base.AutoManipulator):
            @classmethod
            def can_trigger(cls, owner):
                return {}

            def run(self):
                yield self.unit

        manager.auto_manipulators = {
            'AutoMockManipulatorA': AutoMockManipulatorA,
            'AutoMockManipulatorB': AutoMockManipulatorB,
        }
        manager.manipulator_priorities = {
            'AutoMockManipulatorA': -10000,
            'AutoMockManipulatorB': 0,
        }
        # Register auto manipulators without any performance optimization.
        manager.register_auto_manipulators(interval=-1, check_interval=0)
        self.enable_auto_manipulators(manager)

        assert not manager.queue
        assert manager.current_task is None
        manager.update(0.1)
        assert manager.current_task is None
        assert len(manager.queue) == 2
        assert isinstance(manager.manipulator_queue[0][2],
                          AutoMockManipulatorA)
        assert isinstance(manager.manipulator_queue[1][2],
                          AutoMockManipulatorB)
        a1 = manager.manipulator_queue[0][2]
        assert not a1.started
        manager.update(0.2)
        assert manager.current_task is a1
        assert a1.started
        assert not a1.done
        assert len(manager.queue) == 1
        assert isinstance(manager.manipulator_queue[0][2],
                          AutoMockManipulatorB)
        manager.update(0.3)
        assert manager.current_task is a1
        assert a1.done
        assert len(manager.queue) == 1
        assert isinstance(manager.manipulator_queue[0][2],
                          AutoMockManipulatorB)
        # In this time, the manager should finish the execution of a1 and
        # schedule another instance of AutoMockManipulatorA.
        manager.update(0.4)
        assert manager.current_task is None
        assert manager.last_task is a1
        assert len(manager.queue) == 2
        assert isinstance(manager.manipulator_queue[0][2],
                          AutoMockManipulatorA)
        assert isinstance(manager.manipulator_queue[1][2],
                          AutoMockManipulatorB)
        a2 = manager.manipulator_queue[0][2]
        assert a2 is not a1
        assert not a2.started
        manager.update(0.5)
        assert manager.current_task is a2
        assert a2.started
        assert not a2.done
        assert len(manager.queue) == 1
        assert isinstance(manager.manipulator_queue[0][2],
                          AutoMockManipulatorB)

    def test_update_trigger_auto_manipulator_with_monitored_objects(
            self, manager):
        c = manipulators.base.MockAutoManipulator.clone()
        c.mockable_monitored_objects = ['SomeObject']
        manager.auto_manipulators = {
            'MockAutoManipulator': c,
        }
        # Register auto manipulators without any performance optimization.
        manager.register_auto_manipulators(interval=-1, check_interval=0)
        self.enable_auto_manipulators(manager)
        some_object = kcsapi.KCAAObject(generation=1)
        manager.objects['SomeObject'] = some_object
        assert not manager.is_manipulator_scheduled('MockAutoManipulator')
        manager.update(0.1)
        assert manager.is_manipulator_scheduled('MockAutoManipulator')
        manager.update(0.2)
        assert manager.is_manipulator_scheduled('MockAutoManipulator')
        manager.update(0.3)
        # Now the manipulator is done.
        assert not manager.is_manipulator_scheduled('MockAutoManipulator')
        manager.update(0.4)
        assert not manager.is_manipulator_scheduled('MockAutoManipulator')
        # With an update, the manipulator should be run.
        some_object.generation += 1
        manager.update(0.5)
        assert manager.is_manipulator_scheduled('MockAutoManipulator')

    def test_update_resume_auto_manipulators(self, manager):
        manager.auto_manipulators = {
            'MockAutoManipulator':
            manipulators.base.MockAutoManipulator.clone(),
        }
        # Register auto manipulators without any performance optimization.
        manager.register_auto_manipulators(interval=-1, check_interval=0)
        assert not manager.is_manipulator_scheduled('MockAutoManipulator')
        manager.update(0.1)
        assert not manager.is_manipulator_scheduled('MockAutoManipulator')
        self.enable_auto_manipulators(manager)
        manager.update(0.2)
        assert manager.is_manipulator_scheduled('MockAutoManipulator')
        manager.update(0.3)
        m = manager.current_task
        assert isinstance(m, manipulators.base.MockAutoManipulator)
        assert m.run_called

    def test_update_suspend_auto_manipulators(self, manager):
        manager.auto_manipulators = {
            'MockAutoManipulator':
            manipulators.base.MockAutoManipulator.clone(),
        }
        # Register auto manipulators without any performance optimization.
        manager.register_auto_manipulators(interval=-1, check_interval=0)
        self.enable_auto_manipulators(manager)
        assert not manager.is_manipulator_scheduled('MockAutoManipulator')
        manager.update(0.1)
        assert manager.is_manipulator_scheduled('MockAutoManipulator')
        self.enable_auto_manipulators(manager, enabled=False)
        manager.update(0.2)
        assert manager.is_manipulator_scheduled('MockAutoManipulator')
        manager.update(0.3)
        assert not manager.is_manipulator_scheduled('MockAutoManipulator')
        manager.update(0.4)
        assert not manager.is_manipulator_scheduled('MockAutoManipulator')
        self.enable_auto_manipulators(manager)
        manager.update(0.5)
        assert manager.is_manipulator_scheduled('MockAutoManipulator')


def main():
    import doctest
    doctest.testmod(manipulator_util)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
