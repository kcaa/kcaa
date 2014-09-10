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
        logger.info('Trying to rebuild {} with material ships {}.'.format(
            target_ship.name.encode('utf8'),
            ', '.join([s.name.encode('utf8') for s in material_ships])))
        logger.info('Expected gain: {}'.format(
            compute_rebuilding_gain(material_ships).json()))
        if not target_ship.locked:
            logger.error('Target ship is not locked.')
            return
        if target_ship.is_under_repair:
            logger.error('Target ship is under repair.')
            return
        fleet = fleet_list.find_fleet_for_ship(target_ship.id)
        if fleet and fleet.mission_id:
            logger.error('Target ship is undertaking a mission.')
        for material_ship in material_ships:
            name = material_ship.name.encode('utf8')
            if material_ship.locked:
                logger.error('Material ship {} is locked.'.format(name))
                return
            fleet = fleet_list.find_fleet_for_ship(material_ship.id)
            if fleet and fleet.mission_id:
                logger.error('Material ship {} is undertaking a mission.'
                             .format(name))
                return
            if ship_list.is_unique(material_ship):
                logger.error('Material ship {} is unique.'.format(name))
                return
        yield self.screen.change_screen(screens.PORT_REBUILDING)
        fleet = fleet_list.find_fleet_for_ship(target_ship.id)
        if fleet:
            yield self.screen.select_fleet(fleet.id)
            yield self.screen.select_fleet_ship(
                fleet.ship_ids.index(target_ship_id))
        else:
            # First select the first fleet to cancel the effect of page
            # skipping of the last attempt.
            yield self.screen.select_fleet(1)
            yield self.screen.select_ship_list()
            page, in_page_index = (
                ship_list.get_ship_position_rebuilding_target(
                    target_ship_id, fleet_list))
            yield self.screen.select_page(page)
            yield self.screen.select_ship(in_page_index)
        yield self.screen.try_rebuilding()
        for i, material_ship in enumerate(material_ships):
            yield self.screen.select_slot(i)
            max_page = ship_list.max_page_rebuilding(material_ship_ids[:i])
            page, in_page_index = ship_list.get_ship_position_rebuilding(
                material_ship.id, material_ship_ids[:i])
            yield self.screen.select_material_page(page, max_page)
            yield self.screen.select_material_ship(in_page_index)
        yield self.screen.finalyze_rebuilding()
        yield self.screen.confirm_rebuilding()
        yield self.screen.check_rebuilding_result()
        yield self.screen.cancel()


class EnhanceBestShip(base.Manipulator):

    def run(self):
        logger.info(
            'Trying to enhance the best ship which has the room to grow.')
        ship_list = self.objects.get('ShipList')
        if not ship_list:
            logger.error('No ship list was found. Giving up.')
            return
        fleet_list = self.objects.get('FleetList')
        if not fleet_list:
            logger.error('No fleet list was found. Giving up.')
            return
        target_candidates = sorted(
            ship_list.rebuilding_enhanceable_ships(fleet_list),
            ship.compare_ship_by_kancolle_level, reverse=True)
        material_candidates = sorted(
            ship_list.rebuilding_available_material_ships(fleet_list),
            ship.compare_ship_by_rebuilding_rank)
        material_pool = compute_rebuilding_gain(material_candidates)
        logger.debug('Material pool: {}'.format(material_pool.json()))
        for target_ship in target_candidates:
            firepower_room = (target_ship.firepower.maximum -
                              (target_ship.firepower.baseline +
                               target_ship.enhanced_ability.firepower))
            thunderstroke_room = (target_ship.thunderstroke.maximum -
                                  (target_ship.thunderstroke.baseline +
                                   target_ship.enhanced_ability.thunderstroke))
            anti_air_room = (target_ship.anti_air.maximum -
                             (target_ship.anti_air.baseline +
                              target_ship.enhanced_ability.anti_air))
            armor_room = (target_ship.armor.maximum -
                          (target_ship.armor.baseline +
                           target_ship.enhanced_ability.armor))
            firepower_ok = firepower_room > 0 and material_pool.firepower > 0
            thunderstroke_ok = (thunderstroke_room > 0 and
                                material_pool.thunderstroke > 0)
            anti_air_ok = anti_air_room > 0 and material_pool.anti_air > 0
            armor_ok = armor_room > 0 and material_pool.armor > 0
            if (not firepower_ok and not thunderstroke_ok and
                    not anti_air_ok and not armor_ok):
                continue
            material_ships = []
            last_gain = compute_rebuilding_gain([])
            for material_ship in material_candidates:
                gain = compute_rebuilding_gain(
                    material_ships + [material_ship])
                capped_gain = ship.AbilityEnhancement(
                    firepower=min(gain.firepower, firepower_room),
                    thunderstroke=min(gain.thunderstroke, thunderstroke_room),
                    anti_air=min(gain.anti_air, anti_air_room),
                    armor=min(gain.armor, armor_room))
                # There should be additional improvement.
                gain_improvement = (
                    capped_gain.firepower > last_gain.firepower or
                    capped_gain.thunderstroke > last_gain.thunderstroke or
                    capped_gain.anti_air > last_gain.anti_air or
                    capped_gain.armor > last_gain.armor)
                # Anti air and firepower enhancements are relatively rare. Try
                # not to exceed them.
                gain_no_waste = (gain.firepower <= firepower_room and
                                 gain.anti_air <= anti_air_room)
                if gain_improvement and gain_no_waste:
                    material_ships.append(material_ship)
                    last_gain = capped_gain
                if len(material_ships) == 5:
                    break
            else:
                # Using less than 5 ships is considered "mottainai".
                # It may be acceptable when the ship is reaching the enhance
                # limit.
                if (len(material_ship) < 5 and
                        (last_gain.firepower < firepower_room or
                         last_gain.thunderstroke < thunderstroke_room or
                         last_gain.anti_air < anti_air_room or
                         last_gain.armor < armor_room)):
                    continue
            logger.info(
                '{} has the room to grow. firepower: {}, thunderstroke: {}, '
                'anti_air: {}, armor: {}'.format(
                    target_ship.name.encode('utf8'),
                    firepower_room, thunderstroke_room, anti_air_room,
                    armor_room))
            logger.info('Expected capped gain: {}'.format(last_gain.json()))
            yield self.do_manipulator(RebuildShip, target_ship.id,
                                      [s.id for s in material_ships])
            return
        else:
            logger.error('No ship has the room to grow.')
