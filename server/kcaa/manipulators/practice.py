#!/usr/bin/env python

import logging

import base
from kcaa import screens
from kcaa.kcsapi import practice


logger = logging.getLogger('kcaa.manipulators.practice')


class CheckPracticeOpponents(base.Manipulator):

    def run(self):
        logger.info('Checking practice opponents')
        yield self.screen.change_screen(screens.PORT_PRACTICE)
        practice_list = self.objects.get('PracticeList')
        if not practice_list:
            logger.info('No practice list was found. Giving up.')
            return
        for practice_ in practice_list.practices:
            if practice_.result != practice.Practice.RESULT_NEW:
                continue
            yield self.screen.check_opponent(practice_.id)
            yield self.screen.cancel()


class GoOnPractice(base.Manipulator):

    def run(self, fleet_id, practice_id, formation):
        fleet_id = int(fleet_id)
        practice_id = int(practice_id)
        formation = int(formation)
        logger.info(
            'Making the fleet {} go on the practice {} with formation'.format(
                fleet_id, practice_id, formation))
        yield self.screen.change_screen(screens.PORT_PRACTICE)
        practice_list = self.objects.get('PracticeList')
        if not practice_list:
            logger.error('No practice list was found. Giving up.')
            return
        fleet_list = self.objects.get('FleetList')
        if not fleet_list:
            logger.error('No fleet list was found. Giving up.')
            return
        fleet = fleet_list.fleets[fleet_id - 1]
        # TODO: Check if the fleet is avialable for practice. Some ships may be
        # in the repair dock.
        practice_ = practice_list.practices[practice_id - 1]
        if practice_.result != practice.Practice.RESULT_NEW:
            logger.error('Practice {} is already done.'.format(practice_id))
            return
        yield self.screen.check_opponent(practice_.id)
        yield self.screen.try_practice()
        yield self.screen.select_fleet(fleet_id)
        yield self.screen.confirm_practice()
        if len(fleet.ship_ids) >= 4:
            yield self.screen.select_formation(formation)
        # TODO: Handle the battle.
