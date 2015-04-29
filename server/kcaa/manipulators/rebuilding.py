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


class SelectShip(base.Manipulator):

    def run(self, ship_id):
        ship_id = int(ship_id)
        ship_list = self.objects.get('ShipList')
        if not ship_list:
            logger.error('No ship list was found. Giving up.')
            return
        fleet_list = self.objects.get('FleetList')
        if not fleet_list:
            logger.error('No fleet list was found. Giving up.')
            return
        yield self.screen.change_screen(screens.PORT_REBUILDING)
        fleet = fleet_list.find_fleet_for_ship(ship_id)
        if fleet:
            yield self.screen.select_fleet(fleet.id)
            yield self.screen.select_fleet_ship(
                fleet.ship_ids.index(ship_id))
        else:
            # First select the first fleet to cancel the effect of page
            # skipping of the last attempt.
            yield self.screen.select_fleet(1)
            yield self.screen.select_ship_list()
            page, in_page_index = (
                ship_list.get_ship_position_rebuilding_target(
                    ship_id, fleet_list))
            yield self.screen.select_page(page)
            yield self.screen.select_ship(in_page_index)


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
            if material_ship.unique:
                logger.error('Material ship {} is unique.'.format(name))
                return
        yield self.do_manipulator(SelectShip, ship_id=target_ship.id)
        yield self.screen.try_rebuilding()
        for i, material_ship in enumerate(material_ships):
            yield self.screen.select_slot(i)
            max_page = ship_list.max_page_rebuilding(material_ship_ids[:i])
            page, in_page_index = ship_list.get_ship_position_rebuilding(
                material_ship.id, material_ship_ids[:i])
            yield self.screen.select_material_page(page, max_page)
            yield self.screen.select_material_ship(in_page_index)
        yield self.screen.finalize_rebuilding()
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


class RemodelShip(base.Manipulator):

    def run(self, ship_id):
        ship_id = int(ship_id)
        self.require_objects(['ShipList', 'PlayerResources'])
        ship_list = self.objects['ShipList']
        target_ship = ship_list.ships[str(ship_id)]
        logger.info('Remodeling {}'.format(target_ship.name.encode('utf8')))
        if not target_ship.upgrade_to:
            raise Exception('Target ship has no upgrade anymore.')
        if target_ship.level < target_ship.upgrade_level:
            raise Exception(
                'Target ship\'s level is insufficient. Required {}, but has '
                'only {}.'.format(target_ship.upgrade_level,
                                  target_ship.level))
        if target_ship.is_under_repair or target_ship.away_for_mission:
            raise Exception('Target ship is not ready for upgrade.')
        resources = self.objects['PlayerResources']
        # TODO: Maybe factor out to kcsapi/player.py?
        upgrade_resource = target_ship.upgrade_resource
        if (upgrade_resource.fuel > resources.fuel or
                upgrade_resource.ammo > resources.ammo):
            raise Exception(
                'Resource insufficient. Required {} fuel and {} ammo, but has '
                'only {} fuel and {} ammo.'.format(
                    upgrade_resource.fuel, upgrade_resource.ammo,
                    resources.fuel, resources.ammo))
        yield self.screen.change_screen(screens.PORT_REBUILDING)
        yield self.do_manipulator(ClearEquipments, ship_id=target_ship.id)
        # The target ship is still selected after ClearEquipments.
        yield self.screen.try_remodeling()
        yield self.screen.finalize_remodeling()
        yield self.screen.confirm_remodeling()
        yield self.screen.check_remodeling_result()


class ClearEquipments(base.Manipulator):

    def run(self, ship_id):
        ship_id = int(ship_id)
        self.require_objects(['ShipList'])
        ship_list = self.objects['ShipList']
        target_ship = ship_list.ships[str(ship_id)]
        logger.info('Clearing equipments of {}'.format(
            target_ship.name.encode('utf8')))
        if target_ship.is_under_repair or target_ship.away_for_mission:
            raise Exception(
                'Target ship is not ready for equipment replacement.')
        yield self.do_manipulator(SelectShip, ship_id=target_ship.id)
        yield self.screen.clear_all_item_slots(len(target_ship.equipment_ids))


class ReplaceEquipments(base.Manipulator):

    @staticmethod
    def select_equipment_ids(target_ship, equipment_defs, ship_def_list,
                             ship_list, equipment_list):
        if len(target_ship.equipment_ids) != len(equipment_defs):
            logger.error('Equipment list lengths differ ({} vs. {})'.format(
                len(target_ship.equipment_ids), len(equipment_defs)))
            return None
        equipped_item_ids = set()
        for ship in ship_list.ships.itervalues():
            for equipment_id in ship.equipment_ids:
                if equipment_id != -1:
                    equipped_item_ids.add(equipment_id)
        equipment_ids = []
        for i, definition in enumerate(equipment_defs):
            if definition is None:
                equipment_ids.append(-1)
                continue
            ship_type_def = ship_def_list.ship_types[
                str(target_ship.ship_type)]
            if not ship_type_def.loadable_equipment_types[
                    str(definition.type)]:
                logger.error(
                    'Equipment type {} is not loadable to {} ships.'.format(
                        definition.name.encode('utf8'),
                        ship_type_def.name.encode('utf8')))
                return None
            if target_ship.equipment_ids[i] != -1:
                current_equipment = (
                    equipment_list.items[str(target_ship.equipment_ids[i])])
                if current_equipment.item_id == definition.id:
                    equipment_ids.append(current_equipment.id)
                    continue
            if str(definition.id) not in equipment_list.item_instances:
                logger.error('No equipment available.')
                return None
            unequipped_items = [
                equipment_id for equipment_id in
                equipment_list.item_instances[str(definition.id)].item_ids if
                equipment_id not in equipped_item_ids]
            if unequipped_items:
                equipment_ids.append(unequipped_items[0])
                equipped_item_ids.add(unequipped_items[0])
            else:
                # TODO: Use least recently used items in other ships' equipment
                # as well.
                logger.error('No available unequipped item for {}'.format(
                    definition.name.encode('utf8')))
                return None
        return equipment_ids

    @staticmethod
    def filter_out_unloadable(items, target_ship, ship_def_list):
        ship_type_def = ship_def_list.ship_types[str(target_ship.ship_type)]
        return [item for item in items if
                ship_type_def.loadable_equipment_types[str(item.type)]]

    def run(self, ship_id, equipment_definition_ids):
        ship_id = int(ship_id)
        if not isinstance(equipment_definition_ids, list):
            equipment_definition_ids = [
                int(def_id) for def_id in equipment_definition_ids.split(',')]
        ship_def_list = self.objects.get('ShipDefinitionList')
        if not ship_def_list:
            logger.error('No ship definition list was found. Giving up.')
            return
        ship_list = self.objects.get('ShipList')
        if not ship_list:
            logger.error('No ship list was found. Giving up.')
            return
        equipment_def_list = self.objects.get('EquipmentDefinitionList')
        if not equipment_def_list:
            logger.error('No equipment definition list was found. Giving up.')
            return
        equipment_list = self.objects.get('EquipmentList')
        if not equipment_list:
            logger.error('No equipment list was found. Giving up.')
            return
        target_ship = ship_list.ships[str(ship_id)]
        equipment_defs = []
        for i, def_id in enumerate(equipment_definition_ids):
            if def_id == -1:
                equipment_defs.append(None)
            elif def_id == -2:
                # TODO: Consider refactoring. This is duplicating what's in
                # select_equipment_ids().
                if target_ship.equipment_ids[i] == -1:
                    equipment_defs.append(None)
                else:
                    current_equipment = equipment_list.items[
                        str(target_ship.equipment_ids[i])]
                    equipment_defs.append(
                        current_equipment.definition(equipment_def_list))
            else:
                equipment_defs.append(equipment_def_list.items[str(def_id)])
        logger.info('Replace equipments of ship {} ({}) with [{}]'.format(
            target_ship.name.encode('utf8'), target_ship.id,
            ', '.join(equipment_definition.name.encode('utf8') for
                      equipment_definition in equipment_defs if
                      equipment_definition)))
        if target_ship.is_under_repair or target_ship.away_for_mission:
            logger.error('Target ship is not ready for equipment replacement. '
                         'Giving up.')
            return
        equipment_ids = ReplaceEquipments.select_equipment_ids(
            target_ship, equipment_defs, ship_def_list, ship_list,
            equipment_list)
        if not equipment_ids:
            logger.error('No available equipments. Giving up.')
            return
        yield self.do_manipulator(ReplaceEquipmentsByIds,
                                  ship_id=target_ship.id,
                                  equipment_ids=equipment_ids)


class ReplaceEquipmentsByIds(base.Manipulator):

    def run(self, ship_id, equipment_ids):
        ship_def_list = self.objects['ShipDefinitionList']
        ship_list = self.objects['ShipList']
        equipment_def_list = self.objects['EquipmentDefinitionList']
        equipment_list = self.objects['EquipmentList']
        target_ship = ship_list.ships[str(ship_id)]
        equipments = [equipment_list.items[str(e_id)] for e_id in
                      equipment_ids if e_id > 0]
        current_equipment_ids = target_ship.equipment_ids
        current_equipments = [equipment_list.items[str(e_id)] for e_id in
                              current_equipment_ids if e_id > 0]
        logger.info(
            u'Replace equipments of ship {} ({}) [{}] with [{}]'.format(
                target_ship.name, target_ship.id,
                ', '.join([e.definition(equipment_def_list).name for e in
                           current_equipments]),
                ', '.join([e.definition(equipment_def_list).name for e in
                           equipments])))
        logger.debug('Equipment IDs to load: {}'.format(equipment_ids))
        logger.debug('Current equipment IDs: {}'.format(current_equipment_ids))
        if (target_ship.equipment_ids ==
                [e_id if e_id > 0 else -1 for e_id in equipment_ids]):
            logger.info('No change in equipments.')
            return
        if all([equipment_id <= 0 for equipment_id in equipment_ids]):
            yield self.do_manipulator(ClearEquipments, ship_id=ship_id)
            return
        yield self.do_manipulator(SelectShip, ship_id=target_ship.id)
        # For each slot, clear preceding equipments than the targeted
        # equipment.
        # TODO: this logic needs to be tested when the list is just a
        # reordered one of the original (e.g. [1, 2, 3] from [3, 1, 2]).
        # Maybe abstract the scheduler and write tests for them.
        for i, e_id in enumerate(equipment_ids[:-1]):
            if e_id <= 0:
                break
            for j in xrange(i + 1, len(current_equipment_ids)):
                c_id = current_equipment_ids[j]
                if e_id == c_id:
                    logger.debug('Removing {} at slot {}'.format(c_id, j))
                    for _ in xrange(j - i):
                        yield self.screen.clear_item_slot(i)
                    del current_equipment_ids[i:j]
                    current_equipment_ids.extend([-1] * (j - i))
        logger.debug('Current after reorder: {}'.format(current_equipment_ids))
        num_cleared_items = 0
        for slot_index, equipment_id in enumerate(equipment_ids):
            # ID of -1 is considered empty.
            # ID of 0 is considered omittable, which is empty in this context.
            if equipment_id <= 0:
                yield self.screen.clear_item_slot(
                    slot_index - num_cleared_items)
                num_cleared_items += 1
                continue
            if equipment_id == current_equipment_ids[slot_index]:
                continue
            yield self.screen.select_item_slot(slot_index - num_cleared_items)
            unequipped_items = ReplaceEquipments.filter_out_unloadable(
                equipment_list.get_unequipped_items(ship_list), target_ship,
                ship_def_list)
            logger.debug('Trying to set {}'.format(equipment_id))
            page, in_page_index = equipment_list.compute_page_position(
                equipment_id, unequipped_items)
            max_page = equipment_list.get_max_page(unequipped_items)
            if page is None or in_page_index is None:
                for i, equipment in enumerate(unequipped_items):
                    definition = equipment.definition(equipment_def_list)
                    logger.debug(u'{}-{}: {:7d} {} ({}:{})'.format(
                        i / 10, i % 10, equipment.id, definition.name,
                        definition.type, definition.type_name))
                raise Exception('Invalid unequipped items.')
            # TODO: Remove this debug logging after the issue is resolved.
            # Write tests instead.
            logger.debug('position: {}-{}, max page: {}'.format(
                page, in_page_index, max_page))
            for i in xrange(10 * (page - 1), min(10 * page,
                                                 len(unequipped_items))):
                definition = unequipped_items[i].definition(equipment_def_list)
                logger.debug(u'{}-{}: {:7d} {} ({}:{})'.format(
                    page, i - 10 * (page - 1), unequipped_items[i].id,
                    definition.name, definition.type, definition.type_name))
            yield self.screen.select_item_page(page, max_page)
            yield self.screen.select_item(in_page_index)
            yield self.screen.confirm_item_replacement()
            # TODO: Remove this debug logging after the issue is resolved.
            # Re-fetch the updated ship info.
            target_ship = ship_list.ships[str(target_ship.id)]
            actual_id = target_ship.equipment_ids[
                slot_index - num_cleared_items]
            if equipment_id != actual_id:
                for i, equipment in enumerate(unequipped_items):
                    definition = equipment.definition(equipment_def_list)
                    logger.debug(u'{}-{}: {:7d} {} ({}:{})'.format(
                        i / 10, i % 10, equipment.id, definition.name,
                        definition.type, definition.type_name))
                raise Exception(
                    u'Replacement failed. Expected {}, got {}.'.format(
                        equipment_id, actual_id))