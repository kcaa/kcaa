#!/usr/bin/env python

import datetime
import logging
import time

import base
from kcaa import screens
from kcaa.kcsapi import mission


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
        now = int(1000 * time.time())
        count = 0
        for mission_ in mission_list.missions:
            if mission_.eta and mission_.eta - cls.precursor_duration < now:
                count += 1
        if cls.verbose and (count > 0 or
                            now - cls.interval > cls.last_updated):
            cls.last_updated = now
            mission_num = 0
            etas = []
            for mission_ in mission_list.missions:
                if mission_.eta:
                    mission_num += 1
                    etas.append(mission_.eta)
                    logger.debug('ETA{}: {}'.format(
                        mission_num,
                        datetime.datetime.fromtimestamp(mission_.eta / 1000)
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


class FindMission(base.Manipulator):

    def run(self, mission_list, mission_id):
        # MAPAREA_BASE should be already fetched. We start from
        # SOUTHWESTERN_ISLANDS.
        for maparea in xrange(
                mission.Mission.MAPAREA_SOUTHWESTERN_ISLANDS,
                mission.Mission.MAPAREA_SOUTH + 1):
            yield self.screen.select_maparea(maparea)
            if mission_list.get_mission(mission_id):
                return


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
        yield self.screen.change_screen(screens.PORT_MISSION)
        mission_ = mission_list.get_mission(mission_id)
        if mission_:
            yield self.screen.select_maparea(mission_.maparea)
        else:
            yield self.do_manipulator(FindMission, mission_list, mission_id)
            mission_ = mission_list.get_mission(mission_id)
            if not mission_:
                logger.info('Mission {} is unknown. Giving up.'.format(
                    mission_id))
                return
        mission_index = mission_list.get_index_in_maparea(mission_)
        yield self.screen.select_mission(mission_index)
        yield self.screen.confirm()
        yield self.screen.select_fleet(fleet_id)
        yield self.screen.finalize()
