#!/usr/bin/env python

import datetime
import logging

import base
import expedition
import fleet
import logistics
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


class AutoCheckPracticeOpponents(base.ScheduledManipulator):

    @classmethod
    def schedules(cls):
        return [datetime.time(3, 0),
                datetime.time(15, 0)]

    @classmethod
    def random_delay_params(cls):
        return base.GammaDistributedRandomDelayParams(10.0, 30.0, 1800)

    @classmethod
    def wanted_objects(cls):
        return ['PracticeList']

    @classmethod
    def precondition(cls, owner):
        return screens.in_category(owner.screen_id, screens.PORT)

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
        yield self.do_manipulator(organizing.MarkReservedForUse,
                                  ship_ids=fleet_.ship_ids,
                                  reserved_for_use=True)
        yield self.screen.change_screen(screens.PORT_PRACTICE)
        yield self.screen.check_opponent(practice.id)
        # The oppoonent changed the fleet organization. The expected type
        # mismatches -- retry the process from the beginning.
        if practice.fleet_type != expected_fleet_type:
            yield self.screen.cancel()
            yield self.do_manipulator(organizing.MarkReservedForUse,
                                      ship_ids=fleet_.ship_ids,
                                      reserved_for_use=False)
            self.add_manipulator(HandlePractice, fleet_id, practice_id)
            return
        yield self.screen.try_practice()
        yield self.screen.select_fleet(fleet_id)
        yield self.screen.confirm_practice()
        if len(fleet_.ship_ids) >= 4:
            yield self.screen.select_formation(formation)
        yield self.do_manipulator(EngagePractice, formation=formation)
        yield self.do_manipulator(organizing.MarkReservedForUse,
                                  ship_ids=fleet_.ship_ids,
                                  reserved_for_use=False)


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
        ship_list = self.objects.get('ShipList')
        if not ship_list:
            logger.error('No ship list was found. Giving up.')
            return
        ship_def_list = self.objects['ShipDefinitionList']
        equipment_list = self.objects['EquipmentList']
        equipment_def_list = self.objects['EquipmentDefinitionList']
        preferences = self.manager.preferences
        recently_used_equipments = (
            self.manager.states['RecentlyUsedEquipments'])
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
        matching_fleets = [
            sf for sf in self.manager.preferences.fleet_prefs.saved_fleets
            if sf.name == practice_plan.fleet_name]
        if not matching_fleets:
            return
        fleet_deployment = matching_fleets[0]
        if not fleet_deployment.are_all_ships_ready(
                ship_list, ship_def_list, equipment_list, equipment_def_list,
                preferences.equipment_prefs, recently_used_equipments):
            logger.error('Fleet is not ready.')
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


class AutoHandleAllPractices(base.ScheduledManipulator):

    @classmethod
    def schedules(cls):
        return [datetime.time(1, 0),
                datetime.time(13, 0)]

    @classmethod
    def random_delay_params(cls):
        return base.GammaDistributedRandomDelayParams(30.0, 60.0, 3600)

    @classmethod
    def acceptable_delay(cls):
        return datetime.timedelta(minutes=90)

    @classmethod
    def precondition(cls, owner):
        return screens.in_category(owner.screen_id, screens.PORT)

    def run(self):
        yield self.do_manipulator(HandleAllPractices, 1)


class EngagePractice(base.Manipulator):

    def run(self, formation):
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
            battle, ships, formation)
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
        self.add_manipulator(logistics.ChargeFleet, fleet_id=battle.fleet_id)

    def should_go_night_combat(self, battle, ships, formation):
        expected_result = kcsapi.battle.expect_result(
            ships, battle.enemy_ships)
        if expected_result == kcsapi.Battle.RESULT_S:
            logger.debug('No night battle; will achieve S-class victory.')
            return False
        available_ships = [s for s in ships if s.can_attack_midnight]
        if not available_ships:
            logger.debug('No night battle; no ship can attack midnight.')
            return False
        # Target for S-class victory.
        if expedition.EngageExpedition.can_achieve_victory(
                battle, ships, 'S'):
            return True
        # Compromise with an A- or B-class victory.
        if expected_result >= kcsapi.Battle.RESULT_B:
            logger.debug(
                'No night battle; cannot achieve S-class victory, but '
                'anyways, will win.')
            return False
        # Target for B-class victory.
        logger.debug(
            'Night battle; less hope, but possible to achieve B-class '
            'victory.')
        return True
