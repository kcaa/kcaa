#!/usr/bin/env python

import datetime
import heapq
import logging
import traceback

import browser
from kcaa import kcsapi
import manipulators
import screens
import task


def reload_modules():
    reload(manipulators)
    manipulators.reload_modules()


class ScreenManager(object):

    def __init__(self, manipulator_manager):
        self._logger = logging.getLogger('kcaa.manipulator_util')
        self.objects = manipulator_manager.objects
        self.updated_object_types = manipulator_manager.updated_object_types
        self.browser_conn = manipulator_manager.browser_conn
        self.task_manager = manipulator_manager.task_manager
        self._last_screen_id = screens.UNKNOWN
        self._current_screen = manipulators.screen.Screen(self)
        self.define_screens()

    def define_screens(self):
        self.screens = {
            screens.SPECIAL_START: manipulators.screen.StartScreen,
            screens.PORT: manipulators.screen.PortScreen,
            screens.PORT_MAIN: manipulators.screen.PortMainScreen,
            screens.PORT_RECORD: manipulators.screen.PortScreen,
            screens.PORT_ENCYCLOPEDIA: manipulators.screen.PortScreen,
            screens.PORT_ITEMRACK: manipulators.screen.PortScreen,
            screens.PORT_FURNITURE: manipulators.screen.PortScreen,
            screens.PORT_QUESTLIST: manipulators.screen.PortScreen,
            screens.PORT_ITEMSHOP: manipulators.screen.PortScreen,
            screens.PORT_EXPEDITION: manipulators.screen.PortExpeditionScreen,
            screens.PORT_PRACTICE: manipulators.screen.PortPracticeScreen,
            screens.PORT_MISSION: manipulators.screen.PortMissionScreen,
            screens.PORT_ORGANIZING: manipulators.screen.PortOrganizingScreen,
            screens.PORT_LOGISTICS: manipulators.screen.PortLogisticsScreen,
            screens.PORT_REBUILDING: manipulators.screen.PortRebuildingScreen,
            screens.PORT_REBUILDING_REBUILDRESULT:
            manipulators.screen.PortRebuildingScreen,
            screens.PORT_REBUILDING_REMODELRESULT:
            manipulators.screen.PortRebuildingScreen,
            screens.PORT_REPAIR: manipulators.screen.PortRepairScreen,
            screens.PORT_SHIPYARD: manipulators.screen.PortShipyardScreen,
            screens.PORT_SHIPYARD_GETSHIP:
            manipulators.screen.PortShipyardScreen,
            screens.PORT_SHIPYARD_GETEQUIPMENT:
            manipulators.screen.PortShipyardScreen,
            screens.EXPEDITION: manipulators.screen.ExpeditionScreen,
            screens.EXPEDITION_COMPASS: manipulators.screen.ExpeditionScreen,
            screens.EXPEDITION_SAILING: manipulators.screen.ExpeditionScreen,
            screens.EXPEDITION_FORMATION: manipulators.screen.ExpeditionScreen,
            screens.EXPEDITION_COMBAT: manipulators.screen.ExpeditionScreen,
            screens.EXPEDITION_NIGHT: manipulators.screen.ExpeditionScreen,
            screens.EXPEDITION_NIGHTCOMBAT:
            manipulators.screen.ExpeditionScreen,
            screens.EXPEDITION_RESULT: manipulators.screen.ExpeditionScreen,
            screens.EXPEDITION_REWARDS: manipulators.screen.ExpeditionScreen,
            screens.EXPEDITION_CONTINUE: manipulators.screen.ExpeditionScreen,
            screens.EXPEDITION_TERMINAL: manipulators.screen.ExpeditionScreen,
            screens.PRACTICE: manipulators.screen.PracticeScreen,
            screens.PRACTICE_COMBAT: manipulators.screen.PracticeScreen,
            screens.PRACTICE_NIGHT: manipulators.screen.PracticeScreen,
            screens.PRACTICE_NIGHTCOMBAT: manipulators.screen.PracticeScreen,
            screens.PRACTICE_RESULT: manipulators.screen.PracticeScreen,
            screens.MISSION_RESULT: manipulators.screen.MissionResultScreen,
        }

    def click(self, x, y):
        self.browser_conn.send((browser.COMMAND_CLICK, (x, y)))

    def add_task(self, t):
        return self.task_manager.add(t)

    @property
    def current_screen(self):
        return self._current_screen

    def update_screen(self, screen_id=None):
        screen_object = self.objects.get('Screen')
        if not screen_object:
            return
        if screen_id is None:
            screen_id = screen_object.screen
        else:
            screen_object.screen = screen_id
            screen_object.generation += 1
            self.updated_object_types.add('Screen')
        if screen_id != self._last_screen_id:
            screen = self.screens.get(screen_id)
            if screen:
                self._current_screen = screen(self)
                self._logger.debug('Current screen is {}'.format(screen_id))
            else:
                self._logger.debug('Current screen {} is not manipulatable.'
                    .format(screen_id))
                self._current_screen = manipulators.screen.Screen(self)
        self._last_screen_id = screen_id


class ManipulatorManager(object):
    """Creates Kancolle manipulator, which assists user interaction by
    manipulating the Kancolle player (Flash) programatically."""

    def __init__(self, browser_conn, objects, preferences, epoch):
        self._logger = logging.getLogger('kcaa.manipulator_util')
        self.browser_conn = browser_conn
        self.objects = objects
        self.preferences = preferences
        self.initialize(epoch)

    def initialize(self, epoch):
        self.queue = []
        self.queue_count = 0
        self.scheduled_manipulators = {}
        self.running_auto_triggerer = []
        self.current_task = None
        self.last_task = None
        self.updated_object_types = set()
        self.task_manager = task.TaskManager(epoch)
        self.screen_manager = ScreenManager(self)
        self.define_manipulators()
        self.define_auto_manipulators()
        self.register_auto_manipulators()
        self.define_manipulator_priorities()
        self.current_schedule_fragment = None
        self.rmo = kcsapi.client.RunningManipulators()
        self.rmo_last_generation = self.rmo.generation
        self.objects['RunningManipulators'] = self.rmo
        self.set_auto_manipulator_preferences(self.preferences.automan_prefs)

    def define_manipulators(self):
        self.manipulators = {
            # Expedition
            'GoOnExpedition': manipulators.expedition.GoOnExpedition,
            'SailOnExpeditionMap': manipulators.expedition.SailOnExpeditionMap,
            'EngageExpedition': manipulators.expedition.EngageExpedition,
            'WarmUp': manipulators.expedition.WarmUp,
            'WarmUpFleet': manipulators.expedition.WarmUpFleet,
            'WarmUpIdleShips': manipulators.expedition.WarmUpIdleShips,
            # Practice
            'CheckPracticeOpponents':
            manipulators.practice.CheckPracticeOpponents,
            'GoOnPractice': manipulators.practice.GoOnPractice,
            'HandlePractice': manipulators.practice.HandlePractice,
            'HandleAllPractices': manipulators.practice.HandleAllPractices,
            'EngagePractice': manipulators.practice.EngagePractice,
            # Mission
            'GoOnMission': manipulators.mission.GoOnMission,
            # Organizing
            'LoadShips': manipulators.organizing.LoadShips,
            'LoadFleet': manipulators.organizing.LoadFleet,
            'LockShips': manipulators.organizing.LockShips,
            # Logistics
            'ChargeFleet': manipulators.logistics.ChargeFleet,
            # Rebuilding
            'RebuildShip': manipulators.rebuilding.RebuildShip,
            'EnhanceBestShip': manipulators.rebuilding.EnhanceBestShip,
            'ReplaceEquipments': manipulators.rebuilding.ReplaceEquipments,
            # Repair
            'RepairShips': manipulators.repair.RepairShips,
            # Shipyard
            'BuildShip': manipulators.shipyard.BuildShip,
            'ReceiveShip': manipulators.shipyard.ReceiveShip,
            'DevelopEquipment': manipulators.shipyard.DevelopEquipment,
            'DissolveShip': manipulators.shipyard.DissolveShip,
            'DissolveEquipment': manipulators.shipyard.DissolveEquipment,
        }

    def define_auto_manipulators(self):
        self.auto_manipulators = {
            # Expedition
            'AutoWarmUpIdleShips': manipulators.expedition.AutoWarmUpIdleShips,
            # Organizing
            'AutoLockUniqueShips': manipulators.organizing.AutoLockUniqueShips,
            # Logistics
            'AutoChargeFleet': manipulators.logistics.AutoChargeFleet,
            # Rebuilding
            'AutoEnhanceBestShip': manipulators.rebuilding.AutoEnhanceBestShip,
            # Repair
            'AutoRepairShips': manipulators.repair.AutoRepairShips,
            'AutoCheckRepairResult': manipulators.repair.AutoCheckRepairResult,
            # Shipyard
            'AutoReceiveShips': manipulators.shipyard.AutoReceiveShips,
            'AutoDissolveShips': manipulators.shipyard.AutoDissolveShips,
            # Practice
            'AutoCheckPracticeOpponents':
            manipulators.practice.AutoCheckPracticeOpponents,
            'AutoHandleAllPractices':
            manipulators.practice.AutoHandleAllPractices,
            # Mission
            'AutoCheckMissionResult':
            manipulators.mission.AutoCheckMissionResult,
            'AutoGoOnMission': manipulators.mission.AutoGoOnMission,
            # Special
            'AutoStartGame': manipulators.special.AutoStartGame,
        }

    def register_auto_manipulators(self, interval=-1):
        for manipulator in self.auto_manipulators.itervalues():
            self.add_auto_manipulator(manipulator, interval)
        self.suppress_auto_manipulators()

    def define_manipulator_priorities(self):
        # Manipulators not listed here have the default priority of 0.
        # Each manipulator gets a priority less than the parent when invoked
        # with Manipulator.add_manipulator().
        self.manipulator_priorities = {
            # AutoCheckMissionResult has the highest priority because it
            # blocks all other manipulations when coming back to the port main
            # screen.
            'AutoCheckMissionResult': -10000,
            # AutoChargeFleet takes the second highest. This should precede
            # practice or missions.
            'AutoChargeFleet': -9000,
            # AutoLockUniqueShips must precede rebuilding manipulators,
            # especially AutoEnhanceBestShip or the like that may use a new
            # unique ship.
            'AutoLockUniqueShips': -8000,
            # AutoEnhanceBestShip should precede AutoDissolveShips and
            # AutoWarmUpIdleShips, and # recede AutoLockUniqueShips.
            'AutoEnhanceBestShip': -3000,
            # AutoDissolveShips must recede AutoEnhanceBestShip. It is always
            # better to use a ship for enhancement rather than just dissolving
            # it to a small amount of materials.
            'AutoDissolveShips': -2000,
            # AutoCheckRepairResult can be anywhere.
            'AutoCheckRepairResult': -1000,
            # AutoRepairShips should have a lower priority than WarmUp.
            # Priority of -2 ensures that this doesn't bother the current
            # WarmUp call chain, but precedes consequent WarmUp invocations.
            # Note that the top-level WarmUp is called from WarmUpFleet or
            # WarmUpIdleShips, which have priority of -1.
            # TODO: Consider fixing this; this is too hacky. This can be solved
            # by separating the 'hard' version and 'soft' version. Hard version
            # takes higher priority and repairs fatal ships. Soft version has
            # less lower prirority and repairs slightly damages ships when
            # idle.
            'AutoRepairShips': -2,
            # AutoCheckPracticeOpponents runs when idle. It's quick, so it can
            # precede other low priority ones.
            'AutoCheckPracticeOpponents': 1000,
            # AutoHandleAllPractices runs when idle. It may take some time, and
            # thus should precede other time-consuming low priority tasks.
            'AutoHandleAllPractices': 2000,
            # AutoReceiveShips runs when idle.
            'AutoReceiveShips': 8000,
            # AutoGoOnMission should not bother other manipulators. It can run
            # when idle.
            'AutoGoOnMission': 9000,
            # AutoWarmUpIdleShips can run only when idle. Other low priority
            # tasks should usually precede as this would take considerable
            # time.
            'AutoWarmUpIdleShips': 10000,
        }

    def set_auto_manipulator_preferences(self, automan_prefs):
        self.auto_manipulators_enabled = automan_prefs.enabled
        self._logger.info('AutoManipulator {}.'.format(
            'enabled' if automan_prefs.enabled else 'disabled'))
        self.auto_manipulators_schedules = automan_prefs.schedules
        self._logger.info(
            'AutoManipulator schedules: {}.'.format(automan_prefs.schedules))
        seconds_in_today = self.seconds_in_today
        self._logger.info('Current time: {}'.format(seconds_in_today))
        self.current_schedule_fragment = None
        # Update RunningManipulators object.
        self.rmo.auto_manipulators_enabled = automan_prefs.enabled
        self.rmo.auto_manipulators_active = (
            self.are_auto_manipulator_scheduled())
        self.rmo.generation += 1

    @staticmethod
    def in_schedule_fragment(seconds_in_today, schedule_fragment):
        if (seconds_in_today >= schedule_fragment.start and
                seconds_in_today < schedule_fragment.end):
            return True

    @property
    def seconds_in_today(self):
        # TODO: Move this out to util module?
        now = datetime.datetime.now()
        return 3600 * now.hour + 60 * now.minute + now.second

    def are_auto_manipulator_scheduled(self, seconds_in_today=None):
        if not self.auto_manipulators_enabled:
            return False
        if seconds_in_today is None:
            seconds_in_today = self.seconds_in_today
        if self.current_schedule_fragment:
            if ManipulatorManager.in_schedule_fragment(
                    seconds_in_today, self.current_schedule_fragment):
                return True
        self.current_schedule_fragment = None
        for schedule_fragment in self.auto_manipulators_schedules:
            if ManipulatorManager.in_schedule_fragment(seconds_in_today,
                                                       schedule_fragment):
                self.current_schedule_fragment = schedule_fragment
                return True
        return False

    def add_manipulator(self, manipulator):
        t = self.task_manager.add(manipulator)
        t.suspend()
        manipulator_name = manipulator.__class__.__name__
        if manipulator.priority is None:
            manipulator.priority = (
                self.manipulator_priorities.get(manipulator_name, 0))
        entry = (manipulator.priority, self.queue_count, t)
        heapq.heappush(self.queue, entry)
        self.queue_count += 1
        if self.current_task:
            self.update_running_manipulators()
        # Always keep the last entry in scheduled_manipulators.
        # Note that the current task will be the last entry if the same
        # manipulator is recursively called; exclude such case.
        last_entry = self.scheduled_manipulators.get(manipulator_name, None)
        if (not last_entry or last_entry[2] is self.current_task or
                entry > last_entry):
            self.scheduled_manipulators[manipulator_name] = entry
        self.log_manipulator_queue()
        self._logger.debug(
            'Manipulator {} scheduled.'.format(manipulator_name))
        return t

    def is_manipulator_scheduled(self, manipulator_name):
        return manipulator_name in self.scheduled_manipulators

    def add_auto_manipulator(self, auto_manipulator, interval=-1):
        t = self.task_manager.add(manipulators.base.AutoManipulatorTriggerer(
            self, None, auto_manipulator, interval=interval))
        self.running_auto_triggerer.append(t)
        return t

    def leave_port(self):
        if isinstance(self.screen_manager.current_screen,
                      manipulators.screen.PortScreen):
            self.screen_manager.update_screen(screens.PORT)

    def resume_auto_manipulators(self):
        previously_run = True
        for t in self.running_auto_triggerer:
            if not t.running:
                t.resume()
                previously_run = False
        return not previously_run

    def suppress_auto_manipulators(self):
        previously_run = False
        for t in self.running_auto_triggerer:
            if t.running:
                t.suspend()
                previously_run = True
        return previously_run

    def activate_auto_manipulator(self):
        if self.are_auto_manipulator_scheduled():
            if self.resume_auto_manipulators():
                self.leave_port()
                self.rmo.auto_manipulators_active = True
                self.rmo.generation += 1
        else:
            if self.suppress_auto_manipulators():
                self.rmo.auto_manipulators_active = False
                self.rmo.generation += 1

    def update_running_manipulators(self):
        self.rmo.running_manipulator = unicode(
            self.current_task.__class__.__name__, 'utf8')
        self.rmo.manipulators_in_queue = [
            unicode(manipulator.__class__.__name__, 'utf8')
            for p, c, manipulator in self.queue]
        self.rmo.generation += 1

    def log_manipulator_queue(self):
        sorted_queue = self.manipulator_queue
        self._logger.debug('Manipulator queue: [{}]'.format(
            ', '.join(('{} (p{};c{})'.format(m.__class__.__name__, p, c)
                       for p, c, m in sorted_queue))))

    @property
    def manipulator_queue(self):
        return heapq.nsmallest(len(self.queue), self.queue)

    def dispatch(self, command):
        if len(command) != 2:
            raise ValueError(
                'Command should have the type and args: {}'.format(command))
        command_type, command_args = command
        manipulator = self.manipulators.get(command_type)
        if manipulator:
            try:
                self.add_manipulator(manipulator(self, None, **command_args))
            except TypeError:
                raise TypeError(
                    'manipulator argument mismatch. type = {}, args = {}'
                    .format(command_type, command_args))
        else:
            raise ValueError('Unknown command type: {}'.format(command_type))

    def start_task_from_queue(self):
        if self.queue:
            self.log_manipulator_queue()
            priority, queue_count, t = heapq.heappop(self.queue)
            manipulator_name = t.__class__.__name__
            self._logger.debug('Manipulator {} started.'.format(
                manipulator_name))
            self.current_task = t
            t.resume()
            if not self.last_task:
                self.browser_conn.send((browser.COMMAND_COVER, (True,)))
                self.leave_port()
            self.update_running_manipulators()
        else:
            if self.last_task:
                self.browser_conn.send((browser.COMMAND_COVER, (False,)))
                self.rmo.running_manipulator = None
                self.rmo.manipulators_in_queue = []
                self.rmo.generation += 1
            self.current_task = None
            self.last_task = None

    def finish_current_task(self):
        if not self.current_task.success:
            exception = self.current_task.exception
            if exception.message:
                self._logger.error('{}: {}'.format(
                    type(exception).__name__, exception.message))
            else:
                self._logger.error(
                    'Some exception of type {} happened.'.format(
                        type(exception).__name__))
            self._logger.debug(''.join(traceback.format_exception(
                type(exception), exception, self.current_task.traceback)))
        self.last_task = self.current_task
        self.current_task = None
        # This removes the entry when the first instance of the
        # manipulators that share the name have finished.
        manipulator_name = self.last_task.__class__.__name__
        self._logger.debug('Manipulator {} finished.'.format(
            manipulator_name))
        if (self.is_manipulator_scheduled(manipulator_name) and
                self.scheduled_manipulators[manipulator_name][2] is
                self.last_task):
            del self.scheduled_manipulators[manipulator_name]

    def update(self, current):
        """Update manipulators.

        :param float current: Current time in seconds
        :returns: Updated KCSAPI objects
        :rtype: :class:`class:`kcaa.kcsapi.model.KCAAObject`
        """
        self.screen_manager.update_screen()
        self.activate_auto_manipulator()
        if not self.current_task:
            self.start_task_from_queue()
        if (self.current_task and
                self.current_task not in self.task_manager.tasks):
            # The current task has finished.
            # Run this before task_manager.update() to allow high-priority
            # tasks take precedence if they still want to rerun.
            self.finish_current_task()
        self.task_manager.update(current)
        if self.rmo.generation > self.rmo_last_generation:
            self.updated_object_types.add('RunningManipulators')
            self.rmo_last_generation = self.rmo.generation
        updated_objects = [self.objects[object_type] for object_type in
                           self.updated_object_types]
        self.updated_object_types.clear()
        return updated_objects


if __name__ == '__main__':
    import manipulator_util_test
    manipulator_util_test.main()
