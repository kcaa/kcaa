#!/usr/bin/env python

import datetime
import logging
import time

import base
from kcaa import screens


logger = logging.getLogger('kcaa.manipulators.automission')


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
        for _ in xrange(count):
            yield self.do_manipulator(CheckMissionResult)
        yield self.screen.leave_port()
