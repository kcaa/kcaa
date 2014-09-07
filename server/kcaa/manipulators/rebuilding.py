#!/usr/bin/env python

import logging

import base
from kcaa import screens
from kcaa.kcsapi import ship


logger = logging.getLogger('kcaa.manipulators.rebuilding')


def compute_gain_with_bonus(gain):
    return gain + (gain + 1) / 5


def compute_rebuilding_gain(material_ships):
    firepower = sum(s.rebuilding_material.firepower for s in material_ships)
    thunderstroke = sum(s.rebuilding_material.thunderstroke for s in
                        material_ships)
    anti_air = sum(s.rebuilding_material.anti_air for s in material_ships)
    armor = sum(s.rebuilding_material.armor for s in material_ships)
    return ship.AbilityEnhancement(
        firepower=compute_gain_with_bonus(firepower),
        thunderstroke=compute_gain_with_bonus(thunderstroke),
        anti_air=compute_gain_with_bonus(anti_air),
        armor=compute_gain_with_bonus(armor))


class RebuildShip(base.Manipulator):

    def run(self, target_ship_id, material_ship_ids):
        target_ship_id = int(target_ship_id)
        if not isinstance(material_ship_ids, list):
            material_ship_ids = [int(ship_id) for ship_id in
                                 material_ship_ids.split(',')]
        if len(material_ship_ids) == 0 or len(material_ship_ids) > 5:
            logger.error('Needs 1 - 5 material ships.')
            return
        ship_list = self.objects.get('ShipList')
        if not ship_list:
            logger.error('No ship list was found. Giving up.')
            return
        fleet_list = self.objects.get('FleetList')
        if not fleet_list:
            logger.error('No fleet list was found. Giving up.')
            return
        target_ship = ship_list.ships[str(target_ship_id)]
        material_ships = [ship_list.ships[str(ship_id)] for ship_id in
                          material_ship_ids]
        if not target_ship.locked:
            logger.error('Target ship is not locked.')
            return
        if target_ship.is_under_repair:
            logger.error('Target ship is under repair.')
            return
        fleet = fleet_list.find_fleet_for_ship(target_ship.id)
        if fleet and fleet.mission_id:
            logger.error('Target ship is undertaking a mission.')
        if [s for s in material_ships if s.locked]:
            logger.error('At least 1 material ship is locked.')
            return
        if [s for s in material_ships if fleet_list.find_fleet_for_ship(s.id)]:
            logger.error('At least 1 material ship has joined a fleet.')
            return
        logger.info('Rebuilding {} with expected gain {}'.format(
            target_ship.name.encode('utf8'),
            compute_rebuilding_gain(material_ships).json()))
        yield self.screen.change_screen(screens.PORT_REBUILDING)
        if fleet:
            yield self.screen.select_fleet(fleet.id)
            yield self.screen.select_fleet_ship(
                fleet.ship_ids.index(target_ship_id))
        else:
            yield self.screen.select_ship_list()
            # TODO: Handle selecting a ship
        yield self.screen.try_rebuilding()
        for i, material_ship in enumerate(material_ships):
            yield self.screen.select_slot(i)
            # TODO: Handle selecting a ship
        yield self.screen.finalyze_rebuilding()
        yield self.screen.confirm_rebuilding()
        yield self.screen.check_result()
        yield self.screen.cancel()
