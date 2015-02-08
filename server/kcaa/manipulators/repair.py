#!/usr/bin/env python

import logging
import time

import base
from kcaa import screens
from kcaa import kcsapi


logger = logging.getLogger('kcaa.manipulators.repair')


class RepairShips(base.Manipulator):

    def run(self, ship_ids):
        if not isinstance(ship_ids, list):
            ship_ids = [int(ship_id) for ship_id in ship_ids.split(',')]
        ship_list = self.objects.get('ShipList')
        if not ship_list:
            logger.error('No ship list was found. Giving up.')
            return
        fleet_list = self.objects.get('FleetList')
        if not fleet_list:
            logger.error('No fleet list was found. Giving up.')
            return
        repair_dock = self.objects.get('RepairDock')
        if not repair_dock:
            logger.error('No repair dock was found. Giving up.')
            return
        repairable_ship_ids = (
            [s.id for s in ship_list.repairable_ships(fleet_list)])
        ships_to_repair = []
        for ship_id in ship_ids:
            ship_ = ship_list.ships[str(ship_id)]
            if ship_.id not in repairable_ship_ids:
                logger.error('Ship {} is not repairable.'.format(
                    ship_.name.encode('utf8')))
                continue
            ships_to_repair.append(ship_)
        empty_slots = [slot for slot in repair_dock.slots if not slot.in_use]
        if len(ships_to_repair) > len(empty_slots):
            logger.info(
                'Repair of {} ships requested, but only {} repair slots are '
                'available. The rest of ships are kept intact for now.'.format(
                    len(ships_to_repair), len(empty_slots)))
            del ships_to_repair[len(empty_slots):]
        if not ships_to_repair:
            return
        logger.info('Repairing ships {}.'.format(', '.join(
            s.name.encode('utf8') for s in ships_to_repair)))
        yield self.screen.change_screen(screens.PORT_REPAIR)
        for ship_to_repair, empty_slot in zip(ships_to_repair, empty_slots):
            yield self.screen.select_slot(empty_slot.id)
            page, index = ship_list.get_ship_position_repair(ship_to_repair.id,
                                                             fleet_list)
            yield self.screen.select_page(page)
            yield self.screen.select_ship(index)
            yield self.screen.try_repair()
            yield self.screen.confirm_repair()


class AutoRepairShips(base.AutoManipulator):

    @classmethod
    def monitored_objects(cls):
        return ['ShipList', 'FleetList', 'RepairDock']

    @staticmethod
    def get_ships_to_repair(objects):
        ship_list = objects.get('ShipList')
        fleet_list = objects.get('FleetList')
        repair_dock = objects.get('RepairDock')
        empty_slots = [slot for slot in repair_dock.slots if not slot.in_use]
        if not empty_slots:
            return []
        return sorted(
            ship_list.repairable_ships(fleet_list),
            kcsapi.ship.ShipSorter.hitpoint_ratio)[:len(empty_slots)]

    @classmethod
    def can_trigger(cls, owner):
        if not screens.in_category(owner.screen_id, screens.PORT):
            return
        # Once this avoided to trigger when in PORT_REPAIR screen. Probably
        # there was a reason for that. But... what? To avoid collision with
        # repair boost?
        if AutoRepairShips.get_ships_to_repair(owner.objects):
            return {}

    def run(self):
        ship_ids = [s.id for s in
                    AutoRepairShips.get_ships_to_repair(self.objects)]
        # To avoid collision with repair boosts, wait a bit before running.
        if ship_ids and self.screen_id == screens.PORT_REPAIR:
            yield 7.0
        yield self.do_manipulator(RepairShips, ship_ids)


class BoostShipRepairing(base.Manipulator):

    def run(self, slot_id):
        slot_id = int(slot_id)
        self.require_objects(['RepairDock'])
        repair_dock = self.objects['RepairDock']
        logger.info('Boosting the ship repairing at the slot {}'.format(
            slot_id))
        slot_index = slot_id - 1
        slot = repair_dock.slots[slot_index]
        if not slot.in_use:
            raise Exception('Slot {} is empty.'.format(slot_id))
        yield self.screen.change_screen(screens.PORT_REPAIR)
        yield self.screen.boost_repair(slot_index)
        yield self.screen.confirm_boost()


class AutoCheckRepairResult(base.AutoManipulator):

    # Repair can be completed 60 seconds earlier than the reported ETA.
    # This is not mandatory, unlike AutoCheckMissionResult, as the completion
    # of repair does not block anything.
    precursor_duration = 60000

    @classmethod
    def required_objects(cls):
        return ['RepairDock']

    @classmethod
    def can_trigger(cls, owner):
        if not screens.in_category(owner.screen_id, screens.PORT):
            return
        repair_dock = owner.objects.get('RepairDock')
        now = long(1000 * time.time())
        to_check = False
        for slot in repair_dock.slots:
            if slot.in_use and slot.eta - cls.precursor_duration < now:
                to_check = True
        if to_check:
            return {}

    def run(self):
        yield 1.0
        yield self.screen.change_screen(screens.PORT_REPAIR)
