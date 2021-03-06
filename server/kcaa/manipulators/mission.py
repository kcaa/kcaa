#!/usr/bin/env python

import datetime
import logging
import random
import time

import base
import fleet
import logistics
import organizing
from kcaa import screens


logger = logging.getLogger('kcaa.manipulators.mission')


class CheckMissionResult(base.Manipulator):

    def run(self):
        logger.info('Checking mission result')
        yield self.screen.check_mission_result()
        self.add_manipulator(logistics.ChargeAllFleets)


class AutoCheckMissionResult(base.AutoManipulator):

    # Missions can be completed 60 seconds earlier than the reported ETA.
    # As the mission complete screen can block other tasks, this starts 5
    # seconds earlier than that and takes 10 seconds of buffer.
    precursor_duration = 60000
    precursor_extra = 5000

    # Parameters to the gamma distribution that decides the wait duration.
    alpha = 5.0
    beta = 120.0
    max_wait_sec = 1800.0
    next_update = None

    # Verbose logging.
    verbose = False
    datetime_pattern = '%Y-%m-%d %H:%M:%S'
    interval = 10000
    last_updated = 0

    @classmethod
    def check_missions(cls, mission_list, now):
        count = 0
        wait = 10.0
        precursor_total = cls.precursor_duration + cls.precursor_extra
        for mission in mission_list.missions:
            if mission.eta and mission.eta - precursor_total < now:
                count += 1
                if mission.eta - cls.precursor_duration < now:
                    wait = 0.0
        if cls.verbose and (count > 0 or
                            now - cls.interval > cls.last_updated):
            cls.last_updated = now
            mission_num = 0
            etas = []
            for mission in mission_list.missions:
                if mission.eta:
                    mission_num += 1
                    etas.append(mission.eta)
                    logger.debug('ETA{}: {}'.format(
                        mission_num,
                        datetime.datetime.fromtimestamp(mission.eta / 1000)
                        .strftime(cls.datetime_pattern)))
            if etas:
                min_eta = min(etas)
                logger.debug('Left: {:.0f} seconds'.format(
                    (min_eta - now) / 1000))
        return count, wait

    @classmethod
    def required_objects(cls):
        return ['MissionList']

    @classmethod
    def precondition(cls, owner):
        return screens.in_category(owner.screen_id, screens.PORT)

    @classmethod
    def can_trigger(cls, owner):
        now = long(1000 * time.time())
        if cls.next_update and now < cls.next_update:
            return
        mission_list = owner.objects['MissionList']
        count, _ = AutoCheckMissionResult.check_missions(mission_list, now)
        if count == 0:
            cls.next_update = None
            return
        if not cls.next_update:
            wait_sec = random.gammavariate(AutoCheckMissionResult.alpha,
                                           AutoCheckMissionResult.beta)
            wait_sec = min(wait_sec, AutoCheckMissionResult.max_wait_sec)
            cls.next_update = now + long(1000 * wait_sec)
            logger.debug(
                'Completed mission detected. Will check after the random '
                'delay {}.'.format(datetime.timedelta(seconds=wait_sec)))
            return
        cls.next_update = None
        return {}

    def run(self):
        mission_list = self.objects['MissionList']
        now = long(1000 * time.time())
        count, wait = AutoCheckMissionResult.check_missions(mission_list, now)
        if count == 0:
            return
        yield wait
        for _ in xrange(count):
            yield self.do_manipulator(CheckMissionResult)


class AutoRecoverFromMissionResult(base.AutoManipulator):

    @classmethod
    def run_only_when_idle(cls):
        return True

    @classmethod
    def can_trigger(cls, owner):
        if owner.screen_id == screens.MISSION_RESULT:
            return {}

    def run(self):
        while self.screen_id != screens.PORT_RECORD:
            yield self.screen.click_record_button()


class GoOnMission(base.Manipulator):

    def run(self, fleet_id, mission_id):
        fleet_id = int(fleet_id)
        mission_id = int(mission_id)
        logger.info('Making the fleet {} go on the mission {}'.format(
            fleet_id, mission_id))
        mission_list = self.objects['MissionList']
        mission = mission_list.get_mission(mission_id)
        if not mission:
            raise Exception('Mission {} is unknown.')
        if not fleet.are_all_ships_available(self, fleet_id):
            return
        ship_list = self.objects['ShipList']
        fleet_list = self.objects['FleetList']
        ready = True
        ship_ids = fleet_list.fleets[fleet_id - 1].ship_ids
        for ship_id in ship_ids:
            ship = ship_list.ships[str(ship_id)]
            if not ship.resource_full:
                # Do not use unicode string in the exception message. It does
                # not work well with traceback.format_exception().
                logger.error(
                    u'Ship {} ({}) is not loading resources to its full '
                    u'capacity.'.format(ship.name, ship.id))
                ready = False
        if not ready:
            yield self.do_manipulator(logistics.ChargeFleet(fleet_id=fleet_id))
        yield self.do_manipulator(organizing.MarkReservedForUse,
                                  ship_ids=ship_ids,
                                  reserved_for_use=True)
        yield self.screen.change_screen(screens.PORT_MISSION)
        yield self.screen.select_maparea(mission.maparea)
        mission_index = mission_list.get_index_in_maparea(mission)
        yield self.screen.select_mission(mission_index)
        yield self.screen.confirm()
        yield self.screen.select_fleet(fleet_id)
        yield self.screen.finalize()
        yield self.do_manipulator(organizing.MarkReservedForUse,
                                  ship_ids=ship_ids,
                                  reserved_for_use=False)


class AutoGoOnMission(base.AutoManipulator):

    @classmethod
    def required_objects(cls):
        return ['ShipDefinitionList', 'EquipmentList',
                'EquipmentDefinitionList']

    @classmethod
    def monitored_objects(cls):
        return ['ShipList', 'FleetList']

    @staticmethod
    def get_go_on_config(objects, preferences, states):
        fleet_list = objects.get('FleetList')
        ship_list = objects.get('ShipList')
        ship_def_list = objects['ShipDefinitionList']
        equipment_list = objects['EquipmentList']
        equipment_def_list = objects['EquipmentDefinitionList']
        if not preferences.mission_prefs:
            return
        recently_used_equipments = states['RecentlyUsedEquipments']
        go_on_config = {}
        for fleet_ in fleet_list.fleets:
            if fleet_.id == 1 or fleet_.mission_id:
                continue
            # TODO: This is ugly. Consider givin a direct access to Preferences
            # object.
            mission_plan = (
                preferences.mission_prefs.get_mission_plan(fleet_.id))
            if not mission_plan or not mission_plan.enabled:
                continue
            matching_fleets = [
                sf for sf in preferences.fleet_prefs.saved_fleets
                if sf.name == mission_plan.fleet_name]
            if not matching_fleets:
                continue
            fleet_deployment = matching_fleets[0]
            if not fleet_deployment.are_all_ships_ready(
                    ship_list, ship_def_list, equipment_list,
                    equipment_def_list, preferences.equipment_prefs,
                    recently_used_equipments):
                continue
            go_on_config[fleet_.id] = mission_plan
        return go_on_config

    @classmethod
    def can_trigger(cls, owner):
        if not screens.in_category(owner.screen_id, screens.PORT):
            return
        if owner.manager.is_manipulator_scheduled('GoOnMission'):
            return
        if AutoGoOnMission.get_go_on_config(owner.objects,
                                            owner.manager.preferences,
                                            owner.manager.states):
            return {}

    def run(self):
        yield 1.0
        go_on_config = AutoGoOnMission.get_go_on_config(
            self.objects, self.manager.preferences, self.manager.states)
        for fleet_id, mission_plan in go_on_config.iteritems():
            self.add_manipulator(organizing.LoadFleet, fleet_id,
                                 mission_plan.fleet_name.encode('utf8'))
            self.add_manipulator(GoOnMission, fleet_id,
                                 mission_plan.mission_id)
