#!/usr/bin/env python

import logging

import base
import fleet
import organizing
from kcaa import kcsapi
from kcaa import screens


# If the vitality of a ship is less than this number, the ship is considered to
# need an warming up.
WARMUP_VITALITY = 75


logger = logging.getLogger('kcaa.manipulators.expedition')


def can_warm_up(ship_):
    return (ship_.vitality < WARMUP_VITALITY and
            ship_.ready and
            ship_.locked and
            (ship_.level >= 10 or ship_.firepower.current >= 20))


class GoOnExpedition(base.Manipulator):

    def run(self, fleet_id, maparea_id, map_id, formation):
        fleet_id = int(fleet_id)
        maparea_id = int(maparea_id)
        map_id = int(map_id)
        formation = int(formation)
        logger.info(
            'Making the fleet {} go on the expedition {}-{} with the '
            'formation {}'.format(
                fleet_id, maparea_id, map_id, formation))
        # TODO: Move maparea definition to a separate module like kcsapic.
        if maparea_id > kcsapi.Mission.MAPAREA_MIDDLE:
            logger.error('Maparea {} is not supported.'.format(maparea_id))
        if not fleet.are_all_ships_available(self, fleet_id):
            return
        # Check ship slot and equipment slot requiement.
        yield self.screen.change_screen(screens.PORT_EXPEDITION)
        yield self.screen.select_maparea(maparea_id)
        yield self.screen.select_map(map_id)
        yield self.screen.try_expedition()
        yield self.screen.select_fleet(fleet_id)
        yield self.screen.confirm_expedition()
        yield self.do_manipulator(SailOnExpeditionMap, formation=formation)


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
        # TODO: Handle a special sailing animation (e.g. spotter aircraft), if
        # needed. Expedition object should have such information.
        yield 6.0
        if event in (kcsapi.Expedition.EVENT_BATTLE,
                     kcsapi.Expedition.EVENT_BATTLE_BOSS):
            yield 3.0
            fleet = fleet_list.fleets[expedition.fleet_id - 1]
            if len(fleet.ship_ids) >= 4:
                yield self.screen.select_formation(formation)
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
        yield self.screen.wait_transition(screens.EXPEDITION_COMBAT,
                                          timeout=20.0)
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
        to_go_for_night_combat = self.should_go_night_combat(
            expedition, battle, ships)
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
        if expedition_result.got_ship:
            self.screen.update_screen_id(screens.EXPEDITION_REWARDS)
            yield self.screen.dismiss_new_ship()
        if expedition.is_terminal:
            yield self.screen.wait_transition(screens.PORT_MAIN)
            return
        if ships[0].fatal:
            yield self.screen.forcedly_drop_out()
            return
        if self.should_go_next(expedition, battle, ships):
            yield self.screen.go_for_next_battle()
            yield self.do_manipulator(SailOnExpeditionMap, formation=formation)
        else:
            yield self.screen.drop_out()

    def should_go_night_combat(self, expedition, battle, ships):
        expected_result = kcsapi.battle.expect_result(
            ships, battle.enemy_ships)
        if expected_result == kcsapi.Battle.RESULT_S:
            return False
        # TODO: Do not gor for night combat if rest of the enemy ships are
        # submarines.
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
    def can_trigger(cls, owner):
        if not screens.in_category(owner.screen_id, screens.PORT):
            return
        if owner.manager.is_manipulator_scheduled('WarmUp'):
            return
        ship_list = owner.objects.get('ShipList')
        if not ship_list:
            return
        fleet_list = owner.objects.get('FleetList')
        if not fleet_list:
            return
        repair_dock = owner.objects.get('RepairDock')
        if not repair_dock:
            return
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
        yield self.do_manipulator(WarmUpIdleShips, 1, num_ships)
