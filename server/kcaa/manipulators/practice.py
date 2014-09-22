#!/usr/bin/env python

import datetime
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


class AutoCheckPracticeOpponents(base.AutoManipulator):

    schedules = [datetime.time(3, 5),
                 datetime.time(15, 5)]

    next_update = None

    @classmethod
    def can_trigger(cls, owner):
        if not screens.in_category(owner.screen_id, screens.PORT):
            return
        now = datetime.datetime.now()
        if cls.next_update is not None and now < cls.next_update:
            return
        t = now.time()
        for next_schedule in cls.schedules:
            if t < next_schedule:
                cls.next_update = datetime.datetime.combine(
                    now.date(), next_schedule)
                break
        else:
            cls.next_update = datetime.datetime.combine(
                now.date() + datetime.timedelta(days=1), cls.schedules[0])
        logger.debug(
            'Next practice update is scheduled at {}'.format(cls.next_update))
        return {}

    def run(self):
        yield self.do_manipulator(CheckPracticeOpponents)


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
        yield self.do_manipulator(EngagePractice)


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
        fleet_list = self.objects.get('FleetList')
        ship_list = self.objects.get('ShipList')
        if not ship_list:
            logger.error('No ship list was found. Giving up.')
            return
        battle = self.objects.get('Battle')
        if not battle:
            logger.error('No battle was found. Giving up.')
            return
        fleet_ = fleet_list.fleets[battle.fleet_id - 1]
        ships = map(lambda ship_id: ship_list.ships[str(ship_id)],
                    fleet_.ship_ids)
        to_go_for_night_combat = self.should_go_night_combat(
            battle, ships)
        if battle.need_midnight_battle:
            # Clicks every >5 seconds in case a night battle is required for
            # the complete win. Timeout is >5 minutes (5 sec x 60 trials).
            # Note that this may be longer due to wait in engage_night_combat()
            # for example.
            for _ in xrange(60):
                if self.screen_id in (screens.PRACTICE_NIGHTCOMBAT,
                                      screens.PRACTICE_RESULT):
                    break
                if to_go_for_night_combat:
                    yield self.screen.engage_night_combat()
                    yield self.screen.wait_transition(
                        screens.PRACTICE_NIGHTCOMBAT, timeout=5.0,
                        raise_on_timeout=False)
                else:
                    yield self.screen.avoid_night_combat()
                    yield self.screen.wait_transition(
                        screens.PRACTICE_RESULT, timeout=5.0,
                        raise_on_timeout=False)
            else:
                logger.error(
                    'The battle did not finish in 5 minutes. Giving up.')
                return
        yield self.screen.wait_transition(screens.PRACTICE_RESULT,
                                          timeout=300.0)
        yield self.screen.dismiss_result_overview()
        yield self.screen.dismiss_result_details()

    def should_go_night_combat(self, battle, ships):
        expected_result = kcsapi.battle.expect_result(
            ships, battle.enemy_ships)
        if expected_result >= kcsapi.Battle.RESULT_B:
            return False
        # TODO: Do not gor for night combat if rest of the enemy ships are
        # submarines.
        available_ships = [s for s in ships if s.can_attack_midnight]
        if not available_ships:
            return False
        enemy_alive_ships = [s for s in battle.enemy_ships if s.alive]
        if len(available_ships) >= len(enemy_alive_ships) - 1:
            return True
        return False
