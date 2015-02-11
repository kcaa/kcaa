#!/usr/bin/env python

import logging
import time

import base
from kcaa import kcsapi
from kcaa import screens
import organizing


logger = logging.getLogger('kcaa.manipulators.shipyard')


class BuildShip(base.Manipulator):

    def run(self, fuel, ammo, steel, bauxite, grand, material):
        fuel = int(fuel)
        ammo = int(ammo)
        steel = int(steel)
        bauxite = int(bauxite)
        grand = grand is True or grand == 'true'
        material = int(material)
        logger.info('Buliding a {} ship with [{}, {}, {}, {}]'.format(
            'grand' if grand else 'normal', fuel, ammo, steel, bauxite))
        build_dock = self.objects.get('BuildDock')
        if not build_dock:
            logger.error('No build dock was found. Giving up.')
            return
        empty_slots = build_dock.empty_slots
        if not empty_slots:
            logger.error('No empty build slot was found.')
            return
        slot_index = empty_slots[0].id - 1
        if grand:
            if (fuel < 1500 or fuel > 7000 or fuel % 10 != 0 or
                    ammo < 1500 or ammo > 7000 or ammo % 10 != 0 or
                    steel < 2000 or steel > 7000 or steel % 10 != 0 or
                    bauxite < 1000 or bauxite > 7000 or bauxite % 10 != 0 or
                    material not in (1, 20, 100)):
                logger.error('Resource amount is invalid for grand building.')
                return
        else:
            if (fuel < 30 or fuel >= 1000 or
                    ammo < 30 or ammo >= 1000 or
                    steel < 30 or steel >= 1000 or
                    bauxite < 30 or bauxite >= 1000):
                logger.error('Resource amount is invalid for normal building.')
                return
        yield self.screen.change_screen(screens.PORT_SHIPYARD)
        yield self.screen.select_slot(slot_index)
        if grand:
            yield self.screen.try_grand_building()
            yield self.screen.set_material(material)
        yield self.screen.set_resource(grand, fuel, ammo, steel, bauxite)
        yield self.screen.confirm_building()


class BoostShipBuilding(base.Manipulator):

    def run(self, slot_id):
        slot_id = int(slot_id)
        self.require_objects(['BuildDock'])
        build_dock = self.objects['BuildDock']
        logger.info('Boosting the ship building at the slot {}'.format(
            slot_id))
        slot_index = slot_id - 1
        slot = build_dock.slots[slot_index]
        if slot.empty:
            raise Exception('Slot {} is empty.'.format(slot_id))
        now = long(1000 * time.time())
        if slot.completed(now):
            logger.info('Slot {} has completed the build.')
            return
        yield self.screen.change_screen(screens.PORT_SHIPYARD)
        yield self.screen.boost_build(slot_index)
        yield self.screen.confirm_boost()
        yield self.do_manipulator(ReceiveShip, slot_id=slot_id)


class ReceiveShip(base.Manipulator):

    def run(self, slot_id):
        slot_id = int(slot_id)
        yield self.screen.change_screen(screens.PORT_SHIPYARD)
        yield self.screen.select_slot(slot_id - 1)
        yield self.screen.check_ship()
        yield self.do_manipulator(organizing.LockUniqueShips)


class AutoReceiveShips(base.AutoManipulator):

    # Ship buliding are completed on time? At least there is no harm on
    # checking the completion when the reported ETA has come.
    precursor_duration = 0

    @classmethod
    def required_objects(cls):
        return ['BuildDock']

    @classmethod
    def get_receivable_slots(cls, objects):
        build_dock = objects.get('BuildDock')
        now = long(1000 * time.time()) + cls.precursor_duration
        return [slot for slot in build_dock.slots if slot.completed(now)]

    @classmethod
    def can_trigger(cls, owner):
        if not screens.in_category(owner.screen_id, screens.PORT):
            return
        if owner.manager.is_manipulator_scheduled('BoostShipBuilding'):
            return
        if AutoReceiveShips.get_receivable_slots(owner.objects):
            return {}

    def run(self):
        yield 1.0
        for slot in AutoReceiveShips.get_receivable_slots(self.objects):
            yield self.do_manipulator(ReceiveShip, slot_id=slot.id)


class DevelopEquipment(base.Manipulator):

    def run(self, fuel, ammo, steel, bauxite):
        fuel = int(fuel)
        ammo = int(ammo)
        steel = int(steel)
        bauxite = int(bauxite)
        logger.info('Developing an equipment with [{}, {}, {}, {}]'.format(
            fuel, ammo, steel, bauxite))
        if (fuel < 10 or fuel > 300 or
                ammo < 10 or ammo > 300 or
                steel < 10 or steel > 300 or
                bauxite < 10 or bauxite > 300):
            logger.error('Resource amount is invalid for development.')
            return
        yield self.screen.change_screen(screens.PORT_SHIPYARD)
        yield self.screen.try_equipment_development()
        yield self.screen.set_development_resource(fuel, ammo, steel, bauxite)
        yield self.screen.confirm_development()
        yield self.screen.check_equipment()


class DissolveShip(base.Manipulator):

    def run(self, ship_id):
        ship_id = int(ship_id)
        ship_list = self.objects.get('ShipList')
        if not ship_list:
            logger.error('No ship list was found. Giving up.')
            return
        ship = ship_list.ships[str(ship_id)]
        logger.info('Dissolving a ship {} ({})'.format(
            ship.name.encode('utf8'), ship_id))
        # TODO: Check if the ship has a locked equipment.
        if ship.locked or ship.is_under_repair or ship.away_for_mission:
            logger.error('Ship {} ({}) is not ready for dissolution.'.format(
                ship.name.encode('utf8'), ship_id))
            return
        yield self.screen.change_screen(screens.PORT_SHIPYARD)
        yield self.screen.try_dissolution()
        page, index = ship_list.get_ship_position(ship_id)
        yield self.screen.select_page(page, ship_list.max_page)
        yield self.screen.select_ship(index)
        yield self.screen.confirm_dissolution()
        yield self.screen.unfocus_selection()


class DissolveLeastValuableShips(base.Manipulator):

    @staticmethod
    def get_target_ships(ship_list, player_info):
        num_dissolvable = len(ship_list.ships) - (player_info.max_ships - 5)
        if num_dissolvable <= 0:
            return None
        target_ships = sorted(
            ship_list.dissolvable_ships(), kcsapi.ShipSorter.rebuilding_rank)
        return target_ships[:num_dissolvable]

    def run(self):
        target_ships = DissolveLeastValuableShips.get_target_ships(
            self.objects['ShipList'], self.objects['PlayerInfo'])
        if not target_ships:
            return
        for target_ship in target_ships:
            yield self.do_manipulator(DissolveShip, ship_id=target_ship.id)


class AutoDissolveShips(base.AutoManipulator):

    @classmethod
    def monitored_objects(cls):
        return ['ShipList', 'PlayerInfo']

    @classmethod
    def can_trigger(cls, owner):
        if not screens.in_category(owner.screen_id, screens.PORT):
            return
        if (owner.manager.is_manipulator_scheduled('DissolveShip') or
                owner.manager.is_manipulator_scheduled('EnhanceBestShip') or
                owner.manager.is_manipulator_scheduled('AutoEnhanceBestShip')):
            return
        if DissolveLeastValuableShips.get_target_ships(
                owner.objects['ShipList'], owner.objects['PlayerInfo']):
            return {}

    def run(self):
        target_ships = DissolveLeastValuableShips.get_target_ships(
            self.objects['ShipList'], self.objects['PlayerInfo'])
        if not target_ships:
            return
        for target_ship in target_ships:
            yield self.do_manipulator(DissolveShip, ship_id=target_ship.id)


class DissolveEquipment(base.Manipulator):

    def run(self, equipment_ids):
        if not isinstance(equipment_ids, list):
            equipment_ids = [int(equipment_id) for equipment_id in
                             equipment_ids.split(',')]
        equipment_list = self.objects.get('EquipmentList')
        if not equipment_list:
            logger.error('No equipment list was found. Giving up.')
            return
        ship_list = self.objects.get('ShipList')
        if not ship_list:
            logger.error('No ship list was found. Giving up.')
            return
        logger.info('Dissolving equipment {}'.format(', '.join(
            str(equipment_id) for equipment_id in equipment_ids)))
        for equipment_id in equipment_ids:
            if str(equipment_id) not in equipment_list.items:
                logger.error('Equipment ({}) is not found. Giving up.'.format(
                    equipment_id))
                return
            if equipment_list.items[str(equipment_id)].locked:
                logger.error('Equipment ({}) is locked. Giving up.'.format(
                    equipment_id))
                return
        unequipped_items = equipment_list.get_unequipped_items(ship_list)
        while equipment_ids:
            max_page = equipment_list.get_max_page(unequipped_items)
            first_page = max_page
            indices = []
            ids_to_dissolve = set()
            for equipment_id in equipment_ids:
                page, in_page_index = equipment_list.compute_page_position(
                    equipment_id, unequipped_items)
                if page is None:
                    logger.error('Eqiupment ({}) is equipped. Giving up.'
                                 .format(equipment_id))
                    return
                if page < first_page:
                    first_page = page
                    indices = [in_page_index]
                    ids_to_dissolve = set([equipment_id])
                elif page == first_page:
                    indices.append(in_page_index)
                    ids_to_dissolve.add(equipment_id)
            yield self.screen.change_screen(screens.PORT_SHIPYARD)
            yield self.screen.try_item_dissolution()
            yield self.screen.select_item_page(first_page, max_page)
            for in_page_index in indices:
                yield self.screen.select_item(in_page_index)
            yield self.screen.confirm_item_dissolution()
            yield self.screen.unfocus_selection()
            unequipped_items = [item for item in unequipped_items if
                                item.id not in ids_to_dissolve]
            equipment_ids = [equipment_id for equipment_id in equipment_ids if
                             equipment_id not in ids_to_dissolve]
