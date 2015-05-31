#!/usr/bin/env python

import logging
import time

import base
import expedition
import rebuilding
from kcaa import screens
from kcaa import kcsapi


logger = logging.getLogger('kcaa.manipulators.repair')


class RepairShips(base.Manipulator):

    # TODO: Move this to the preferences.
    clear_items_before_repair = True

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
        if RepairShips.clear_items_before_repair:
            for ship_to_repair in ships_to_repair:
                yield self.do_manipulator(rebuilding.ClearEquipments,
                                          ship_id=ship_to_repair.id)
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
        ship_list = objects['ShipList']
        fleet_list = objects['FleetList']
        repair_dock = objects['RepairDock']
        empty_slots = [slot for slot in repair_dock.slots if not slot.in_use]
        if not empty_slots:
            return []
        candidate_ships = sorted(
            [s for s in ship_list.repairable_ships(fleet_list) if
             not s.reserved_for_use],
            kcsapi.ship.ShipSorter.hitpoint_ratio)
        # First choose ships that cannot warm up anymore.
        ships_to_repair = [s for s in candidate_ships if
                           not expedition.can_warm_up(s)]
        # Then include everything else.
        ships_to_repair += [s for s in candidate_ships if
                            s not in ships_to_repair]
        return ships_to_repair[:len(empty_slots)]

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


class AutoBoostShipRepairing(base.AutoManipulator):

    # TODO: Move this to preferences
    # Boost threshold in milliseconds. (6 hours)
    boost_threshold = 21600000

    @classmethod
    def monitored_objects(cls):
        return ['RepairDock']

    @classmethod
    def can_trigger(cls, owner):
        if not screens.in_category(owner.screen_id, screens.PORT):
            return
        repair_dock = owner.objects['RepairDock']
        now = long(1000 * time.time())
        for slot in repair_dock.slots:
            if slot.in_use and now + cls.boost_threshold < slot.eta:
                return {'slot_id': slot.id}

    def run(self, slot_id):
        yield self.do_manipulator(BoostShipRepairing, slot_id=slot_id)


class AutoCheckRepairResult(base.AutoManipulator):

    # Repair can be completed 60 seconds earlier than the reported ETA.
    # This is not mandatory, unlike AutoCheckMissionResult, as the completion
    # of repair does not block anything.
    precursor_duration = 60000

    @classmethod
    def monitored_objects(cls):
        return ['RepairDock']

    @classmethod
    def precondition(cls, owner):
        return screens.in_category(owner.screen_id, screens.PORT)

    @classmethod
    def can_trigger(cls, owner):
        repair_dock = owner.objects['RepairDock']
        now = long(1000 * time.time())
        to_check = False
        for slot in repair_dock.slots:
            if slot.in_use and slot.eta - cls.precursor_duration < now:
                to_check = True
        if to_check:
            return {}

    def run(self):
        yield 1.0
        if self.screen_id == screens.PORT_REPAIR:
            yield self.screen.change_screen(screens.PORT_MAIN)
        yield self.screen.change_screen(screens.PORT_REPAIR)
