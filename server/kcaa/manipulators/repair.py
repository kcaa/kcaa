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
    def can_trigger(cls, owner):
        if not screens.in_category(owner.screen_id, screens.PORT):
            return
        if owner.screen_id == screens.PORT_REPAIR:
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
        empty_slots = [slot for slot in repair_dock.slots if not slot.in_use]
        if not empty_slots:
            return
        ships_to_repair = sorted(
            ship_list.repairable_ships(fleet_list),
            kcsapi.ship.compare_ship_by_hitpoint_ratio)[:len(empty_slots)]
        if ships_to_repair:
            return {'ship_ids': [s.id for s in ships_to_repair]}

    def run(self, ship_ids):
        yield self.do_manipulator(RepairShips, ship_ids)


class AutoCheckRepairResult(base.AutoManipulator):

    # Repair can be completed 60 seconds earlier than the reported ETA.
    # This is not mandatory, unlike AutoCheckMissionResult, as the completion
    # of repair does not block anything.
    precursor_duration = 60000

    @classmethod
    def can_trigger(cls, owner):
        if not screens.in_category(owner.screen_id, screens.PORT):
            return
        repair_dock = owner.objects.get('RepairDock')
        if not repair_dock:
            return
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
