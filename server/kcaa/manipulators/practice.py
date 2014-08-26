#!/usr/bin/env python

import logging

import base
import organizing
from kcaa import screens
from kcaa.kcsapi import practice


logger = logging.getLogger('kcaa.manipulators.practice')


class CheckPracticeOpponents(base.Manipulator):

    def run(self):
        logger.info('Checking practice opponents')
        yield self.screen.change_screen(screens.PORT_PRACTICE)
        practice_list = self.objects.get('PracticeList')
        if not practice_list:
            logger.error('No practice list was found. Giving up.')
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
            'Making the fleet {} go on the practice {} with formation {}'
            .format(fleet_id, practice_id, formation))
        practice_list = self.objects.get('PracticeList')
        if not practice_list:
            logger.error('No practice list was found. Giving up.')
            return
        practice_ = practice_list.practices[practice_id - 1]
        if practice_.result != practice.Practice.RESULT_NEW:
            logger.error('Practice {} is already done.'.format(practice_id))
            return
        expected_fleet_type = practice_.fleet_type
        fleet_list = self.objects.get('FleetList')
        if not fleet_list:
            logger.error('No fleet list was found. Giving up.')
            return
        fleet = fleet_list.fleets[fleet_id - 1]
        # TODO: Check if the fleet is avialable for practice. Some ships may be
        # in the repair dock.
        yield self.screen.change_screen(screens.PORT_PRACTICE)
        yield self.screen.check_opponent(practice_.id)
        # The oppoonent changed the fleet organization. The expected type
        # mismatches -- retry the process from the beginning.
        if practice_.fleet_type != expected_fleet_type:
            yield self.screen.cancel()
            self.add_manipulator(HandlePractice, fleet_id, practice_id)
            return
        yield self.screen.try_practice()
        yield self.screen.select_fleet(fleet_id)
        yield self.screen.confirm_practice()
        if len(fleet.ship_ids) >= 4:
            yield self.screen.select_formation(formation)
        self.add_manipulator(EngagePractice)


class HandlePractice(base.Manipulator):

    def run(self, fleet_id, practice_id):
        fleet_id = int(fleet_id)
        practice_id = int(practice_id)
        practice_list = self.objects.get('PracticeList')
        if not practice_list:
            logger.error('No practice list was found. Giving up.')
            return
        practice_ = practice_list.practices[practice_id - 1]
        if practice_.result != practice.Practice.RESULT_NEW:
            logger.error('Practice {} is already done.'.format(practice_id))
            return
        practice_plan = (
            self.manager.preferences.practice_prefs.get_practice_plan(
                practice_.fleet_type))
        if not practice_plan:
            logger.error(
                'No practice plan for the opponent fleet type {}'.format(
                    practice_.fleet_type))
            return
        self.add_manipulator(organizing.LoadFleet, fleet_id,
                             practice_plan.fleet_name.encode('utf8'))
        self.add_manipulator(GoOnPractice, fleet_id, practice_id,
                             practice_plan.formation)
        yield 0.0


class EngagePractice(base.Manipulator):

    def run(self):
        yield self.screen.wait_transition(screens.PRACTICE_COMBAT,
                                          timeout=10.0)
        logger.info('Engaging an enemy fleet in practice.')
        # TODO: Better handle the wait. Especially, if a battle ship is present
        # this will much longer.
        yield self.screen.wait_transition(screens.PRACTICE_RESULT,
                                          timeout=90.0, raise_on_timeout=False)
        if self.screen_id != screens.PRACTICE_RESULT:
            # TODO: Decide whether to go for the night combat depending on the
            # expected result.
            logger.info('Going for the night combat.')
            self.screen.update_screen_id(screens.PRACTICE_NIGHT)
            yield self.screen.engage_night_combat()
            yield self.screen.wait_transition(screens.PRACTICE_RESULT,
                                              timeout=60.0)
        yield self.screen.dismiss_result_overview()
        yield self.screen.dismiss_result_details()
