#!/usr/bin/env python

import logging

import base
import fleet
import organizing
from kcaa import kcsapi
from kcaa import screens


logger = logging.getLogger('kcaa.manipulators.practice')


class CheckPracticeOpponents(base.Manipulator):

    def run(self):
        logger.info('Checking practice opponents')
        yield self.screen.change_screen(screens.PORT_PRACTICE)
        practice_list = self.objects.get('PracticeList')
        if not practice_list:
            logger.error('No practice list was found. Giving up.')
            return
        for practice in practice_list.practices:
            if practice.result != kcsapi.Practice.RESULT_NEW:
                continue
            yield self.screen.check_opponent(practice.id)
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
        practice = practice_list.practices[practice_id - 1]
        if practice.result != kcsapi.Practice.RESULT_NEW:
            logger.error('Practice {} is already done.'.format(practice_id))
            return
        expected_fleet_type = practice.fleet_type
        if not fleet.are_all_ships_available(self, fleet_id):
            return
        fleet_list = self.objects.get('FleetList')
        fleet_ = fleet_list.fleets[fleet_id - 1]
        # TODO: Check if the fleet is avialable for practice. Some ships may be
        # in the repair dock.
        yield self.screen.change_screen(screens.PORT_PRACTICE)
        yield self.screen.check_opponent(practice.id)
        # The oppoonent changed the fleet organization. The expected type
        # mismatches -- retry the process from the beginning.
        if practice.fleet_type != expected_fleet_type:
            yield self.screen.cancel()
            self.add_manipulator(HandlePractice, fleet_id, practice_id)
            return
        yield self.screen.try_practice()
        yield self.screen.select_fleet(fleet_id)
        yield self.screen.confirm_practice()
        if len(fleet_.ship_ids) >= 4:
            yield self.screen.select_formation(formation)
        self.add_manipulator(EngagePractice)


class HandlePractice(base.Manipulator):

    def run(self, fleet_id, practice_id):
        fleet_id = int(fleet_id)
        practice_id = int(practice_id)
        logger.info('Handling practice {} with fleet {}'.format(
            practice_id, fleet_id))
        practice_list = self.objects.get('PracticeList')
        if not practice_list:
            logger.error('No practice list was found. Giving up.')
            return
        practice = practice_list.practices[practice_id - 1]
        if practice.result != kcsapi.Practice.RESULT_NEW:
            logger.error('Practice {} is already done.'.format(practice_id))
            return
        practice_plan = (
            self.manager.preferences.practice_prefs.get_practice_plan(
                practice.fleet_type))
        if not practice_plan:
            logger.error(
                'No practice plan for the opponent fleet type {}'.format(
                    practice.fleet_type))
            return
        self.add_manipulator(organizing.LoadFleet, fleet_id,
                             practice_plan.fleet_name.encode('utf8'))
        self.add_manipulator(GoOnPractice, fleet_id, practice_id,
                             practice_plan.formation)
        yield 0.0


class HandleAllPractices(base.Manipulator):

    def run(self, fleet_id):
        fleet_id = int(fleet_id)
        logger.info('Handling all practice with fleet {}'.format(fleet_id))
        yield self.do_manipulator(CheckPracticeOpponents)
        practice_list = self.objects.get('PracticeList')
        if not practice_list:
            logger.error('No practice list was found. Giving up.')
            return
        for i, practice in enumerate(practice_list.practices):
            if practice.result != kcsapi.Practice.RESULT_NEW:
                continue
            self.add_manipulator(HandlePractice, fleet_id, i + 1)


class EngagePractice(base.Manipulator):

    def run(self):
        yield self.screen.wait_transition(screens.PRACTICE_COMBAT,
                                          timeout=10.0)
        logger.info('Engaging an enemy fleet in practice.')
        # Clicks every >5 seconds in case a night battle is required for the
        # complete win. Timeout is >5 minutes (5 sec x 60 trials).
        # Note that this may be longer due to wait in engage_night_combat()
        # for example.
        for _ in xrange(60):
            if self.screen_id == screens.PRACTICE_NIGHTCOMBAT:
                break
            yield self.screen.wait_transition(
                screens.PRACTICE_RESULT, timeout=5.0, raise_on_timeout=False)
            if self.screen_id == screens.PRACTICE_RESULT:
                break
            # TODO: Decide whether to go for the night combat depending on the
            # expected result.
            yield self.screen.engage_night_combat()
        else:
            logger.error('The battle did not finish in 5 minutes. Giving up.')
            return
        yield self.screen.wait_transition(screens.PRACTICE_RESULT,
                                          timeout=180.0)
        yield self.screen.dismiss_result_overview()
        yield self.screen.dismiss_result_details()
