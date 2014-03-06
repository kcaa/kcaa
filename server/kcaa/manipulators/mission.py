#!/usr/bin/env python

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
            if mission.eta and mission.eta < now:
                count += 1
        if count != 0:
            return {'count': count}

    def run(self, count):
        for _ in xrange(count):
            yield self.do_manipulator(CheckMissionResult)
