#!/usr/bin/env python

import datetime
import logging
import time

import base
import fleet
import organizing
from kcaa import screens


logger = logging.getLogger('kcaa.manipulators.mission')


class CheckMissionResult(base.Manipulator):

    def run(self):
        logger.info('Checking mission result')
        yield self.screen.check_mission_result()


class AutoCheckMissionResult(base.AutoManipulator):

    # Missions can be completed 60 seconds earlier than the reported ETA?
    precursor_duration = 60000

    # Verbose logging.
    verbose = False
    datetime_pattern = '%Y-%m-%d %H:%M:%S'
    interval = 10000
    last_updated = 0

    @classmethod
    def can_trigger(cls, owner):
        if not screens.in_category(owner.screen_id, screens.PORT):
            return
        mission_list = owner.objects.get('MissionList')
        if not mission_list:
            return
        now = long(1000 * time.time())
        count = 0
        for mission in mission_list.missions:
            if mission.eta and mission.eta - cls.precursor_duration < now:
                count += 1
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
        if count != 0:
            return {'count': count}

    def run(self, count):
        yield 1.0
        for _ in xrange(count):
            yield self.do_manipulator(CheckMissionResult)


class GoOnMission(base.Manipulator):

    def run(self, fleet_id, mission_id):
        fleet_id = int(fleet_id)
        mission_id = int(mission_id)
        logger.info('Making the fleet {} go on the mission {}'.format(
            fleet_id, mission_id))
        mission_list = self.objects.get('MissionList')
        if not mission_list:
            logger.info('No mission list was found. Giving up.')
            return
        if not fleet.are_all_ships_available(self, fleet_id):
            return
        yield self.screen.change_screen(screens.PORT_MISSION)
        mission = mission_list.get_mission(mission_id)
        if not mission:
            logger.error('Mission {} is unknown. Giving up.'.format(
                mission_id))
        yield self.screen.select_maparea(mission.maparea)
        mission_index = mission_list.get_index_in_maparea(mission)
        yield self.screen.select_mission(mission_index)
        yield self.screen.confirm()
        yield self.screen.select_fleet(fleet_id)
        yield self.screen.finalize()


class AutoGoOnMission(base.AutoManipulator):

    @classmethod
    def can_trigger(cls, owner):
        if not screens.in_category(owner.screen_id, screens.PORT):
            return
        if owner.manager.is_manipulator_scheduled('GoOnMission'):
            return
        fleet_list = owner.objects.get('FleetList')
        if not fleet_list:
            return
        ship_list = owner.objects.get('ShipList')
        if not ship_list:
            return
        if not owner.manager.preferences.mission_prefs:
            return
        go_on_config = {}
        for fleet_ in fleet_list.fleets:
            if fleet_.id == 1 or fleet_.mission_id:
                continue
            # TODO: This is ugly. Consider givin a direct access to Preferences
            # object.
            mission_plan = (
                owner.manager.preferences.mission_prefs.get_mission_plan(
                    fleet_.id))
            if not mission_plan:
                continue
            matching_fleets = [
                sf for sf in owner.manager.preferences.fleet_prefs.saved_fleets
                if sf.name == mission_plan.fleet_name]
            if not matching_fleets:
                continue
            fleet_deployment = matching_fleets[0]
            if not fleet_deployment.are_all_ships_ready(ship_list):
                continue
            go_on_config[fleet_.id] = mission_plan
        if go_on_config:
            return {'go_on_config': go_on_config}

    def run(self, go_on_config):
        yield 1.0
        for fleet_id, mission_plan in go_on_config.iteritems():
            self.add_manipulator(organizing.LoadFleet, fleet_id,
                                 mission_plan.fleet_name.encode('utf8'))
            self.add_manipulator(GoOnMission, fleet_id,
                                 mission_plan.mission_id)
