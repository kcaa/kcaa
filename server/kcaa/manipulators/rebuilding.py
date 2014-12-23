#!/usr/bin/env python

import logging

import base
from kcaa import screens
from kcaa import kcsapi


logger = logging.getLogger('kcaa.manipulators.rebuilding')


# If some primary attribute (firepower, thunderstroke, anti air or armor) has
# less than this amount in the total room to grow, accept wasting the resource
# for the sake of other growable resources.
ACCEPTABLE_RANGE_FOR_WASTING = 10


def compute_gain_with_bonus(gain):
    return gain + (gain + 1) / 5


def compute_total_room(target_ships):
    firepower, thunderstroke, anti_air, armor = 0, 0, 0, 0
    for target_ship in target_ships:
        gain_cap = compute_gain_cap(target_ship)
        firepower += gain_cap.firepower
        thunderstroke += gain_cap.thunderstroke
        anti_air += gain_cap.anti_air
        armor += gain_cap.armor
    return kcsapi.AbilityEnhancement(
        firepower=firepower,
        thunderstroke=thunderstroke,
        anti_air=anti_air,
        armor=armor)


def compute_rebuilding_gain(material_ships):
    firepower = sum(s.rebuilding_material.firepower for s in material_ships)
    thunderstroke = sum(s.rebuilding_material.thunderstroke for s in
                        material_ships)
    anti_air = sum(s.rebuilding_material.anti_air for s in material_ships)
    armor = sum(s.rebuilding_material.armor for s in material_ships)
    return kcsapi.AbilityEnhancement(
        firepower=compute_gain_with_bonus(firepower),
        thunderstroke=compute_gain_with_bonus(thunderstroke),
        anti_air=compute_gain_with_bonus(anti_air),
        armor=compute_gain_with_bonus(armor))


def compute_gain_cap(target_ship):
    return kcsapi.AbilityEnhancement(
        firepower=(target_ship.firepower.maximum -
                   (target_ship.firepower.baseline +
                    target_ship.enhanced_ability.firepower)),
        thunderstroke=(target_ship.thunderstroke.maximum -
                       (target_ship.thunderstroke.baseline +
                        target_ship.enhanced_ability.thunderstroke)),
        anti_air=(target_ship.anti_air.maximum -
                  (target_ship.anti_air.baseline +
                   target_ship.enhanced_ability.anti_air)),
        armor=(target_ship.armor.maximum -
               (target_ship.armor.baseline +
                target_ship.enhanced_ability.armor)))


def can_enhance(gain_cap, material_pool):
    return ((gain_cap.firepower > 0 and material_pool.firepower > 0) or
            (gain_cap.thunderstroke > 0 and material_pool.thunderstroke > 0) or
            (gain_cap.anti_air > 0 and material_pool.anti_air > 0) or
            (gain_cap.armor > 0 and material_pool.armor > 0))


def compute_capped_gain(gain, gain_cap):
    return kcsapi.AbilityEnhancement(
        firepower=min(gain.firepower, gain_cap.firepower),
        thunderstroke=min(gain.thunderstroke, gain_cap.thunderstroke),
        anti_air=min(gain.anti_air, gain_cap.anti_air),
        armor=min(gain.armor, gain_cap.armor))


def has_improvement(gain_a, gain_b):
    """Returns True if gain_a has at least 1 improvement in any parameter
    compared to gain_b."""
    return (gain_a.firepower > gain_b.firepower or
            gain_a.thunderstroke > gain_b.thunderstroke or
            gain_a.anti_air > gain_b.anti_air or
            gain_a.armor > gain_b.armor)


def reached_cap(gain_cap, gain):
    """Returns True if the given gain has at least 1 non-zero gain that reaches
    the capped gain."""
    return ((gain.firepower > 0 and gain.firepower == gain_cap.firepower) or
            (gain.thunderstroke > 0 and
                gain.thunderstroke == gain_cap.thunderstroke) or
            (gain.anti_air > 0 and gain.anti_air == gain_cap.anti_air) or
            (gain.armor > 0 and gain.armor == gain_cap.armor))


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

    @staticmethod
    def get_target_and_materials(objects):
        ship_list = objects.get('ShipList')
        if not ship_list:
            logger.error('No ship list was found. Giving up.')
            return None, None
        fleet_list = objects.get('FleetList')
        if not fleet_list:
            logger.error('No fleet list was found. Giving up.')
            return None, None
        target_candidates = sorted(
            ship_list.rebuilding_enhanceable_ships(fleet_list),
            kcsapi.ShipSorter.kancolle_level, reverse=True)
        total_room = compute_total_room(target_candidates)
        firepower_wastable = (
            total_room.firepower <= ACCEPTABLE_RANGE_FOR_WASTING)
        anti_air_wastable = (
            total_room.anti_air <= ACCEPTABLE_RANGE_FOR_WASTING)
        material_candidates = sorted(
            ship_list.rebuilding_available_material_ships(fleet_list),
            kcsapi.ShipSorter.rebuilding_rank)
        material_pool = compute_rebuilding_gain(material_candidates)
        logger.debug('Material pool: {}'.format(material_pool.json()))
        for target_ship in target_candidates:
            gain_cap = compute_gain_cap(target_ship)
            if not can_enhance(gain_cap, material_pool):
                continue
            material_ships = []
            last_gain = compute_rebuilding_gain([])
            for material_ship in material_candidates:
                gain = compute_rebuilding_gain(
                    material_ships + [material_ship])
                capped_gain = compute_capped_gain(gain, gain_cap)
                # There should be additional improvement.
                # Even that's true, anti air and firepower enhancements are
                # relatively rare. Try not to exceed them.
                gain_no_waste = (
                    (firepower_wastable or
                     gain.firepower <= gain_cap.firepower) and
                    (anti_air_wastable or
                     gain.anti_air <= gain_cap.anti_air))
                if has_improvement(capped_gain, last_gain) and gain_no_waste:
                    material_ships.append(material_ship)
                    last_gain = capped_gain
                # If the least useful material becomes a mere waste due to the
                # newly added material, remove it from the list.
                while len(material_ships) > 1:
                    gain_r = compute_rebuilding_gain(material_ships[1:])
                    capped_gain_r = compute_capped_gain(gain_r, gain_cap)
                    if has_improvement(capped_gain, capped_gain_r):
                        break
                    # Now the first material ship turned to be a mere waste;
                    # there is no drop in gain even it is removed.
                    del material_ships[0]
                if len(material_ships) == 5:
                    break
            else:
                # Using less than 5 ships is considered "mottainai".
                # It may be acceptable when the ship is reaching the enhance
                # limit.
                if (len(material_ships) < 5 and
                        not reached_cap(gain_cap, last_gain)):
                    continue
            logger.info('{} has the room to grow: {}'.format(
                target_ship.name.encode('utf8'), gain_cap.json()))
            logger.info('Expected capped gain: {}'.format(last_gain.json()))
            return target_ship, material_ships
        else:
            return None, None

    def run(self):
        logger.info(
            'Trying to enhance the best ship which has the room to grow.')
        target_ship, material_ships = (
            EnhanceBestShip.get_target_and_materials(self.objects))
        if target_ship:
            yield self.do_manipulator(RebuildShip, target_ship.id,
                                      [s.id for s in material_ships])
        else:
            logger.error('No ship has the room to grow.')


class AutoEnhanceBestShip(base.AutoManipulator):

    @classmethod
    def monitored_objects(cls):
        return ['ShipList', 'PlayerInfo']

    @classmethod
    def can_trigger(cls, owner):
        if (owner.screen_id != screens.PORT_MAIN and
                owner.screen_id != screens.PORT_REBUILDING):
            return
        ship_list = owner.objects.get('ShipList')
        player_info = owner.objects.get('PlayerInfo')
        if player_info.max_ships - len(ship_list.ships) >= 5:
            return
        target_ship, _ = EnhanceBestShip.get_target_and_materials(
            owner.objects)
        if target_ship:
            return {}

    def run(self):
        yield self.do_manipulator(EnhanceBestShip)
