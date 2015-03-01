#!/usr/bin/env python

import logging

import base
import fleet
import logistics
import mission
import organizing
from kcaa import kcsapi
from kcaa import screens


# If the vitality of a ship is less than this number, the ship is considered to
# need an warming up.
WARMUP_VITALITY = 75


logger = logging.getLogger('kcaa.manipulators.expedition')


# TODO: Check if the admiral can go to the destination. That should be in
# PlayerInfo.
def is_valid_destination_map(maparea_id, map_id):
    # TODO: Check if the event is running.
    if maparea_id == 'E' and map_id >= 1 and map_id <= 5:
        return True
    maparea_id = int(maparea_id)
    return (maparea_id >= 1 and maparea_id <= 6 and
            map_id >= 1 and map_id <= 5)


# TODO: Generalize?
def get_supporting_fleet_mission_id(maparea_id, to_boss):
    if maparea_id == 'E':
        return 142 if to_boss else 141
    maparea_id = int(maparea_id)
    if maparea_id == 5:
        return 34 if to_boss else 33
    raise Exception('Invalid maparea_id: {}'.format(maparea_id))


def can_warm_up(ship_):
    return (ship_.vitality < WARMUP_VITALITY and
            ship_.ready and
            ship_.locked and
            (ship_.level >= 10 or ship_.firepower.current >= 20))


class GoOnExpedition(base.Manipulator):

    def run(self, fleet_id, maparea_id, map_id, formation):
        fleet_id = int(fleet_id)
        if maparea_id != 'E':
            maparea_id = int(maparea_id)
        map_id = int(map_id)
        formation = int(formation)
        logger.info(
            'Making the fleet {} go on the expedition {}-{} with the '
            'formation {}'.format(
                fleet_id, maparea_id, map_id, formation))
        # TODO: Move maparea definition to a separate module like kcsapic.
        if not is_valid_destination_map(maparea_id, map_id):
            raise Exception('Maparea {} is not supported.'.format(maparea_id))
        if not fleet.are_all_ships_available(self, fleet_id):
            raise Exception(
                'Not all ships in the fleet {} is not ready.'.format(
                    fleet_id))
        # Check ship slot and equipment slot requiement.
        yield self.screen.change_screen(screens.PORT_EXPEDITION)
        yield self.screen.select_maparea(maparea_id)
        yield self.screen.select_map(maparea_id, map_id)
        yield self.screen.try_expedition()
        yield self.screen.select_fleet(fleet_id)
        yield self.screen.confirm_expedition()
        yield self.do_manipulator(SailOnExpeditionMap, formation=formation)


class HandleExpeditionCombinedFleet(base.Manipulator):

    def run(self, saved_combined_fleet_name, maparea_id, map_id, formation):
        if isinstance(saved_combined_fleet_name, str):
            saved_combined_fleet_name = saved_combined_fleet_name.decode(
                'utf8')
        if maparea_id != 'E':
            maparea_id = int(maparea_id)
        map_id = int(map_id)
        formation = int(formation)
        logger.info(
            u'Making the combined fleet {} go on the expedition {}-{} with '
            u'the formation {}'.format(
                saved_combined_fleet_name, maparea_id, map_id, formation))
        assert formation >= 11 and formation <= 14
        if not is_valid_destination_map(maparea_id, map_id):
            raise Exception('Maparea {} is not supported.'.format(maparea_id))
        ship_list = self.objects['ShipList']
        fleet_list = self.objects['FleetList']
        matching_fleets = [
            sf for sf in (
                self.manager.preferences.fleet_prefs.saved_combined_fleets) if
            sf.name == saved_combined_fleet_name]
        if not matching_fleets:
            return
        combined_fleet_deployment = matching_fleets[0]
        id_list = combined_fleet_deployment.get_ships(
            ship_list, fleet_list, self.manager.preferences)
        if not id_list.loadable:
            raise Exception(u'Combined fleet {} is not loadable.'.format(
                saved_combined_fleet_name))
        # Reverse the fleet IDs for easier popping.
        fleet_ids = list(reversed(id_list.available_fleet_ids))
        # TODO: Use LoadFleet instead of LoadShips. LoadFleet takes care of
        # equipment deployment.
        # Primary fleet.
        self.add_manipulator(organizing.LoadShips, fleet_id=fleet_ids.pop(),
                             ship_ids=id_list.primary_ship_ids)
        # Secondary fleet.
        if id_list.secondary_ship_ids:
            self.add_manipulator(organizing.LoadShips,
                                 fleet_id=fleet_ids.pop(),
                                 ship_ids=id_list.secondary_ship_ids)
            self.add_manipulator(
                organizing.FormCombinedFleet,
                fleet_type=combined_fleet_deployment.combined_fleet_type)
        else:
            self.screen.change_screen(screens.PORT_ORGANIZING)
            self.screen.dissolve_combined_fleet()
        # Escoting fleet.
        if id_list.escoting_ship_ids:
            escoting_fleet_id = fleet_ids.pop()
            self.add_manipulator(organizing.LoadShips,
                                 fleet_id=escoting_fleet_id,
                                 ship_ids=id_list.escoting_ship_ids)
        # Supporting fleet.
        if id_list.supporting_ship_ids:
            supporting_fleet_id = fleet_ids.pop()
            self.add_manipulator(organizing.LoadShips,
                                 fleet_id=supporting_fleet_id,
                                 ship_ids=id_list.supporting_ship_ids)
        # Escoting and/or supporting fleet missions.
        if id_list.escoting_ship_ids:
            self.add_manipulator(
                mission.GoOnMission,
                fleet_id=escoting_fleet_id,
                mission_id=get_supporting_fleet_mission_id(maparea_id, False))
        if id_list.supporting_ship_ids:
            self.add_manipulator(
                mission.GoOnMission,
                fleet_id=supporting_fleet_id,
                mission_id=get_supporting_fleet_mission_id(maparea_id, True))
        # Finally, go on the mission!
        self.add_manipulator(GoOnExpedition, fleet_id=1, maparea_id=maparea_id,
                             map_id=map_id, formation=formation)
        yield 0.0


class SailOnExpeditionMap(base.Manipulator):

    def run(self, formation):
        yield self.screen.wait_transition(screens.EXPEDITION, timeout=10.0)
        expedition = self.objects.get('Expedition')
        if not expedition:
            logger.error('No expedition info was found. Giving up.')
            return
        fleet_list = self.objects.get('FleetList')
        if not fleet_list:
            logger.error('No fleet list was found. Giving up.')
            return
        if expedition.needs_compass:
            self.screen.update_screen_id(screens.EXPEDITION_COMPASS)
            yield self.screen.roll_compass()
        # Save the current info early not to be overwritten.
        event = expedition.event
        is_terminal = expedition.is_terminal
        self.screen.update_screen_id(screens.EXPEDITION_SAILING)
        yield 6.0
        if event in (kcsapi.Expedition.EVENT_BATTLE,
                     kcsapi.Expedition.EVENT_BATTLE_BOSS):
            yield 3.0
            fleet = fleet_list.fleets[expedition.fleet_id - 1]
            # If some special animation (e.g. spotter aircraft) happens, there
            # would be some additional delay before we can choose the
            # formation. Work around this by waiting some more time if the
            # screen transition has not succeeded.
            for _ in xrange(5):
                if len(fleet.ship_ids) >= 4:
                    yield self.screen.select_formation(formation)
                yield self.screen.wait_transition(
                    screens.EXPEDITION_COMBAT, timeout=3.0,
                    raise_on_timeout=False)
                if self.screen_id in (screens.EXPEDITION_COMBAT,
                                      screens.EXPEDITION_NIGHTCOMBAT):
                    break
            else:
                logger.error('Cannot transitioned to the combat. Giving up.')
                return
            yield self.do_manipulator(EngageExpedition, formation=formation)
            return
        if is_terminal:
            self.screen.update_screen_id(screens.EXPEDITION_TERMINAL)
            yield self.screen.proceed_terminal_screen()
            return
        # This cell is a nonterminal cell without a battle. The next KCSAPI
        # /api_req_map/next should be received. Iterate on.
        yield self.do_manipulator(SailOnExpeditionMap, formation=formation)


class EngageExpedition(base.Manipulator):

    def run(self, formation):
        # The screen must be EXPEDITION_COMBAT or EXPEDITION_NIGHTCOMBAT at
        # this moment. The caller must ensure this assumption is always true.
        # TODO: Handle the event boss battle properly.
        logger.info('Engaging an enemy fleet in expedition.')
        expedition = self.objects.get('Expedition')
        fleet_list = self.objects.get('FleetList')
        ship_list = self.objects.get('ShipList')
        if not ship_list:
            logger.error('No ship list was found. Giving up.')
            return
        battle = self.objects.get('Battle')
        if not battle:
            logger.error('No battle was found. Giving up.')
            return
        fleet_ = fleet_list.fleets[expedition.fleet_id - 1]
        ships = map(lambda ship_id: ship_list.ships[str(ship_id)],
                    fleet_.ship_ids)
        midnight_battle_ships = ships
        secondary_ships = []
        if fleet_list.combined:
            secondary_ships = [ship_list.ships[str(ship_id)] for ship_id in
                               fleet_list.fleets[1].ship_ids]
            midnight_battle_ships = secondary_ships
        to_go_for_night_combat = self.should_go_night_combat(
            expedition, battle, midnight_battle_ships, formation)
        if to_go_for_night_combat:
            logger.info('Going for the night combat.')
        else:
            logger.info('Avoiding the night combat.')
        if battle.need_midnight_battle:
            # Clicks every >5 seconds in case a night battle is required for
            # the complete win. Timeout is >5 minutes (5 sec x 60 trials).
            # Note that this may be longer due to wait in engage_night_combat()
            # for example.
            for _ in xrange(60):
                if self.screen_id in (screens.EXPEDITION_NIGHTCOMBAT,
                                      screens.EXPEDITION_RESULT):
                    break
                if to_go_for_night_combat:
                    yield self.screen.engage_night_combat()
                    yield self.screen.wait_transition(
                        screens.EXPEDITION_NIGHTCOMBAT, timeout=5.0,
                        raise_on_timeout=False)
                else:
                    yield self.screen.avoid_night_combat()
                    yield self.screen.wait_transition(
                        screens.EXPEDITION_RESULT, timeout=5.0,
                        raise_on_timeout=False)
            else:
                logger.error(
                    'The battle did not finish in 5 minutes. Giving up.')
                return
        yield self.screen.wait_transition(screens.EXPEDITION_RESULT,
                                          timeout=300.0)
        expedition_result = self.objects.get('ExpeditionResult')
        if not expedition_result:
            logger.error('No expedition result was found. Giving up.')
            return
        yield self.screen.dismiss_result_overview()
        yield self.screen.dismiss_result_details()
        if fleet_list.combined:
            yield 5.0
            yield self.screen.dismiss_result_details()
        if expedition_result.got_ship:
            self.screen.update_screen_id(screens.EXPEDITION_REWARDS)
            yield self.screen.dismiss_new_ship()
        if expedition.is_terminal:
            yield self.screen.wait_transition(screens.PORT_MAIN)
            self.add_manipulator(logistics.ChargeFleet,
                                 fleet_id=expedition.fleet_id)
            return
        if ships[0].fatal:
            yield self.screen.forcedly_drop_out()
            self.add_manipulator(logistics.ChargeFleet,
                                 fleet_id=expedition.fleet_id)
            return
        # TODO: Handle the case where there is the headquarter equipped by the
        # flagship and there is a healthy destroyer in the secondary fleet.
        if self.should_go_next(expedition, battle, ships + secondary_ships):
            yield self.screen.go_for_next_battle()
            yield self.do_manipulator(SailOnExpeditionMap, formation=formation)
        else:
            yield self.screen.drop_out()
            self.add_manipulator(logistics.ChargeFleet,
                                 fleet_id=expedition.fleet_id)

    def should_go_night_combat(self, expedition, battle, ships, formation):
        expected_result = kcsapi.battle.expect_result(
            ships, battle.enemy_ships)
        if expected_result == kcsapi.Battle.RESULT_S:
            return False
        # TODO: Do not gor for night combat if rest of the enemy ships are
        # submarines.
        # TODO: Move FORMATION enums from prefs and use here.
        # If the formation is the horizontal line, the intention is most likely
        # to avoid the night battle; to avoid damage as much as possible, or to
        # fight against submarines.
        if formation == 4:
            return False
        available_ships = [s for s in ships if s.can_attack_midnight]
        if not available_ships:
            return False
        enemy_alive_ships = [s for s in battle.enemy_ships if s.alive]
        if len(available_ships) >= len(enemy_alive_ships) - 1:
            return True
        if expedition.event == kcsapi.Expedition.EVENT_BATTLE_BOSS:
            return True
        return False

    def should_go_next(self, expedition, battle, ships):
        # TODO: Should go next even if the flagship of the secondary fleet is
        # fatal.
        fatal_ships = [s for s in ships if s.fatal]
        return not fatal_ships


class WarmUp(base.Manipulator):

    def run(self, fleet_id):
        fleet_id = int(fleet_id)
        if not fleet.are_all_ships_available(self, fleet_id):
            return
        ship_list = self.objects.get('ShipList')
        fleet_list = self.objects.get('FleetList')
        fleet_ = fleet_list.fleets[fleet_id - 1]
        if len(fleet_.ship_ids) != 1:
            logger.error('More than 1 ship in the fleet {} will not work.'
                         .format(fleet_id))
            return
        # TODO: Move this kind of conversion to fleet module.
        ships = map(lambda ship_id: ship_list.ships[str(ship_id)],
                    fleet_.ship_ids)
        if ships[0].vitality < WARMUP_VITALITY:
            logger.info('Warming up {}.'.format(ships[0].name.encode('utf8')))
            self.add_manipulator(GoOnExpedition, fleet_id, 1, 1, 0)
            self.add_manipulator(WarmUp, fleet_id)
        yield 0.0


class WarmUpFleet(base.Manipulator):

    def run(self, fleet_id):
        fleet_id = int(fleet_id)
        ok, good_ships, bad_ships = fleet.classify_ships(self, fleet_id)
        good_ships = filter(lambda s: s.vitality < WARMUP_VITALITY, good_ships)
        if not ok or len(good_ships) == 0:
            return
        fleet_list = self.objects.get('FleetList')
        fleet_ = fleet_list.fleets[fleet_id - 1]
        logger.info('Warming up the fleet {}.'.format(fleet_id))
        ship_ids_in_fleet = fleet_.ship_ids[:]
        for good_ship in good_ships:
            self.add_manipulator(organizing.LoadShips,
                                 fleet_id, [good_ship.id])
            self.add_manipulator(WarmUp, fleet_id)
        self.add_manipulator(organizing.LoadShips, fleet_id, ship_ids_in_fleet)
        yield 0.0


class WarmUpIdleShips(base.Manipulator):

    def run(self, fleet_id, num_ships):
        fleet_id = int(fleet_id)
        num_ships = int(num_ships)
        ok, _, _ = fleet.classify_ships(self, fleet_id)
        if not ok:
            return
        ship_list = self.objects.get('ShipList')
        candidate_ships = sorted(
            ship_list.ships.itervalues(),
            kcsapi.ship.ShipSorter.kancolle_level, reverse=True)
        ships_to_warm_up = []
        for candidate_ship in candidate_ships:
            if len(ships_to_warm_up) >= num_ships:
                break
            if not can_warm_up(candidate_ship):
                continue
            ships_to_warm_up.append(candidate_ship)
        if not ships_to_warm_up:
            logger.error('No ship is idle or can warm up.')
            return
        logger.info('Warming up idle ships: {}'.format(', '.join(
            s.name.encode('utf8') for s in ships_to_warm_up)))
        for ship_to_warm_up in ships_to_warm_up:
            self.add_manipulator(organizing.LoadShips,
                                 fleet_id, [ship_to_warm_up.id])
            self.add_manipulator(WarmUp, fleet_id)
        yield 0.0


class AutoWarmUpIdleShips(base.AutoManipulator):

    @classmethod
    def monitored_objects(cls):
        return ['ShipList', 'FleetList', 'RepairDock']

    @classmethod
    def can_trigger(cls, owner):
        # This could interefere with ship build result screen or rebuilding
        # result screen, but that should be suppressed by detecting manual
        # operations.
        if not screens.in_category(owner.screen_id, screens.PORT):
            return
        if owner.manager.is_manipulator_scheduled('WarmUp'):
            return
        ship_list = owner.objects.get('ShipList')
        fleet_list = owner.objects.get('FleetList')
        repair_dock = owner.objects.get('RepairDock')
        # Do not run when no repair slot is available; a ship may be damaged
        # during warming up, and this could pile up damaged ships.
        # Note that ships that are scheduled for repair may not be in the slots
        # yet at this time (right after getting back to port). They will be
        # added by AutoRepairShips.
        empty_slots = [slot for slot in repair_dock.slots if not slot.in_use]
        ships_to_repair = ship_list.repairable_ships(fleet_list)
        ships_to_warm_up = [s for s in ship_list.ships.itervalues() if
                            can_warm_up(s)]
        if len(empty_slots) > len(ships_to_repair) and ships_to_warm_up:
            return {'num_ships': min(len(empty_slots) - len(ships_to_repair),
                                     len(ships_to_warm_up))}

    def run(self, num_ships):
        yield self.do_manipulator(WarmUpIdleShips, 1, min(num_ships, 1))


# TODO: Handle the case where there is the headquarter equipped by the flagship
# and there is a healthy destroyer in the secondary fleet.
# TODO: Should not trigger even if the flagship of the secondary fleet is
# fatal.
class AutoReturnWithFatalShip(base.AutoManipulator):

    @classmethod
    def required_objects(cls):
        return ['ShipList', 'FleetList']

    @classmethod
    def monitored_objects(cls):
        return ['ExpeditionResult']

    @classmethod
    def can_trigger(cls, owner):
        if owner.screen_id != screens.EXPEDITION_RESULT:
            return
        if owner.manager.is_manipulator_scheduled('EngageExpedition'):
            return
        ship_list = owner.objects['ShipList']
        fleet_list = owner.objects['FleetList']
        expedition = owner.objects['Expedition']
        if expedition.is_terminal:
            return
        fleet = fleet_list.fleets[expedition.fleet_id - 1]
        ships = [ship_list.ships[str(ship_id)] for ship_id in fleet.ship_ids]
        if fleet_list.combined:
            secondary_fleet = fleet_list.fleets[1]
            secondary_ships = [ship_list.ships[str(ship_id)] for ship_id in
                               secondary_fleet.ship_ids]
            ships.extend(secondary_ships)
        if any([ship.fatal for ship in ships]):
            return {'combined': fleet_list.combined}

    def run(self, combined):
        yield self.screen.dismiss_result_overview()
        yield self.screen.dismiss_result_details()
        if combined:
            yield self.screen.dismiss_result_details()
        while self.screen_id != screens.PORT_MAIN:
            yield 3.0
            yield self.screen.drop_out()
