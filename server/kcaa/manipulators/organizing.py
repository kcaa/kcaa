#!/usr/bin/env python

import logging

import base
import rebuilding
from kcaa import kcsapi
from kcaa import screens


logger = logging.getLogger('kcaa.manipulators.organization')


class LoadShips(base.Manipulator):
    """Load the given ships to the fleet.

    This markes loaded ships as reserved for use."""

    def run(self, fleet_id, ship_ids):
        fleet_id = int(fleet_id)
        if not isinstance(ship_ids, list):
            ship_ids = [int(ship_id) for ship_id in ship_ids.split(',')]
        ship_ids = [ship_id for ship_id in ship_ids if ship_id > 0]
        ship_list = self.objects['ShipList']
        fleet_list = self.objects['FleetList']
        fleet = fleet_list.fleets[fleet_id - 1]
        if fleet.mission_id:
            logger.error('Fleet is away for mission.')
            return
        if ship_ids == fleet.ship_ids:
            logger.info('All ships are already standing by.')
            return
        # TODO: Ensure the sort mode is Lv in the Kancolle player?
        ships = [ship_list.ships.get(str(ship_id)) for ship_id in ship_ids]
        if any([s is None for s in ships]):
            raise Exception('Some ships are missing.')
        if any([s.away_for_mission for s in ships]):
            raise Exception('Some ships are away for mission.')
        yield self.do_manipulator(MarkReservedForUse,
                                  ship_ids=ship_ids,
                                  reserved_for_use=True)
        yield self.screen.change_screen(screens.PORT_ORGANIZING)
        yield self.screen.select_fleet(fleet_id)
        # Be sure to get the fleet again here, because the Fleet object is
        # recreated (though FleetList itself is just updated).
        # Assuming the fleet object itself is not replaced from now on.
        # This may break when KCSAPI changes -- beware!
        fleet = fleet_list.fleets[fleet_id - 1]
        num_ships_in_fleet = len(fleet.ship_ids)
        # Replace ships with desired ones.
        for pos, ship_id in enumerate(ship_ids):
            fleet_list_generation = fleet_list.generation
            # Desired ships is already present; skipping.
            if (pos < num_ships_in_fleet and
                    fleet.ship_ids[pos] == ship_id):
                continue
            page, index = ship_list.get_ship_position(ship_id)
            yield self.screen.change_member(pos)
            yield self.screen.select_page(page, ship_list.max_page)
            yield self.screen.select_ship(index)
            yield self.screen.confirm()
            while fleet_list.generation == fleet_list_generation:
                yield self.unit
            if fleet.ship_ids[pos] != ship_id:
                logger.debug(repr(fleet.ship_ids))
                raise Exception(
                    'Failed to change the ship to {}. Currently you have {}.'
                    .format(ship_id, fleet.ship_ids[pos]))
        num_ships = len(ship_ids)
        # Remove unnecessary ships.
        if num_ships == 1:
            yield self.screen.detach_all_ships()
        else:
            for _ in xrange(num_ships_in_fleet - num_ships):
                yield self.screen.change_member(num_ships)
                yield self.screen.select_ship(-1)


class LoadFleetByEntries(base.Manipulator):

    @staticmethod
    def compute_others_equipments(equipment_entries, ship_list,
                                  equipment_list):
        equipment_id_to_ships = (
            equipment_list.get_equipment_id_to_ships(ship_list))
        ship_to_cleared = {}
        for entry in equipment_entries:
            ship, equipments = entry
            if not ship or not equipments:
                continue
            logger.debug(u'Ship {} ({}) equipment change:'.format(
                ship.name, ship.id))
            logger.debug('  Current: [{}]'.format(', '.join(
                [str(e_id) for e_id in ship.equipment_ids])))
            logger.debug('  Next:    [{}]'.format(', '.join(
                [str(e.id) for e in equipments])))
            for equipment in equipments:
                equipping_ship = equipment_id_to_ships.get(equipment.id)
                # Compare IDs, not object references, because an update to
                # ShipList can recreate a new instances of ships. Such an
                # update will happen if there is change in the fleet members.
                if equipping_ship and equipping_ship.id != ship.id:
                    ship_to_cleared.setdefault(equipping_ship, set()).add(
                        equipment.id)
                    logger.debug(
                        u'Dismantle equipment {} from ship {} ({})'.format(
                            equipment.id, equipping_ship.name,
                            equipping_ship.id))
        ship_to_equipment_ids = {}
        for s, equipment_ids_to_clear in ship_to_cleared.iteritems():
            ship_to_equipment_ids[s] = [
                e_id if e_id not in equipment_ids_to_clear else -1 for e_id in
                s.equipment_ids]
        return ship_to_equipment_ids

    def run(self, fleet_id, entries):
        ship_list = self.objects['ShipList']
        equipment_list = self.objects['EquipmentList']
        yield self.do_manipulator(LoadShips,
                                  fleet_id=fleet_id,
                                  ship_ids=[e[0].id for e in entries])
        # Clear equipments currently equipped by other ships.
        for s, equipment_ids in LoadFleetByEntries.compute_others_equipments(
                entries, ship_list, equipment_list).iteritems():
            yield self.do_manipulator(rebuilding.ReplaceEquipmentsByIds,
                                      ship_id=s.id,
                                      equipment_ids=equipment_ids)
        # Load the equipments.
        for entry in entries:
            if not entry[1]:
                continue
            equipment_ids = [e.id for e in entry[1]]
            yield self.do_manipulator(rebuilding.ReplaceEquipmentsByIds,
                                      ship_id=entry[0].id,
                                      equipment_ids=equipment_ids)


class LoadFleet(base.Manipulator):

    def run(self, fleet_id, saved_fleet_name):
        fleet_id = int(fleet_id)
        unicode_fleet_name = saved_fleet_name.decode('utf8')
        logger.info('Loading saved fleet {} to fleet {}'.format(
            saved_fleet_name, fleet_id))
        ship_list = self.objects['ShipList']
        ship_def_list = self.objects['ShipDefinitionList']
        equipment_list = self.objects['EquipmentList']
        equipment_def_list = self.objects['EquipmentDefinitionList']
        recently_used_equipments = (
            self.manager.states['RecentlyUsedEquipments'])
        preferences = self.manager.preferences
        matching_fleets = [
            sf for sf in self.manager.preferences.fleet_prefs.saved_fleets
            if sf.name == unicode_fleet_name]
        if not matching_fleets:
            return
        fleet_deployment = matching_fleets[0]
        ship_pool = [s for s in ship_list.ships.values() if
                     not s.reserved_for_use]
        equipment_pool = equipment_list.get_available_equipments(
            recently_used_equipments, ship_list)
        entries = fleet_deployment.get_ships(
            ship_pool, equipment_pool, ship_def_list, equipment_list,
            equipment_def_list, preferences.equipment_prefs)
        if fleet_id in (1, 2):
            yield self.do_manipulator(DissolveCombinedFleet)
        yield self.do_manipulator(LoadFleetByEntries,
                                  fleet_id=fleet_id,
                                  entries=entries)


class DissolveCombinedFleet(base.Manipulator):

    def run(self):
        fleet_list = self.objects['FleetList']
        if fleet_list.combined:
            yield self.screen.change_screen(screens.PORT_ORGANIZING)
            yield self.screen.dissolve_combined_fleet()


class LockShips(base.Manipulator):

    def run(self, ship_ids, locked):
        if not isinstance(ship_ids, list):
            ship_ids = [int(ship_id) for ship_id in ship_ids.split(',')]
        if not isinstance(locked, bool):
            locked = locked == 'true'
        ship_list = self.objects.get('ShipList')
        if not ship_list:
            logger.error('No ship list was found. Giving up.')
            return
        ships = [ship_list.ships[str(ship_id)] for ship_id in ship_ids]
        if not [s for s in ships if s.locked != locked]:
            logger.error('All ships are already {}.'.format(
                'locked' if locked else 'unlocked'))
            return
        yield self.screen.change_screen(screens.PORT_ORGANIZING)
        yield self.screen.change_member(0)
        for ship_id in ship_ids:
            page, index = ship_list.get_ship_position(ship_id)
            yield self.screen.select_page(page, ship_list.max_page)
            yield self.screen.toggle_lock(index)
            ship = ship_list.ships[str(ship_id)]
            if ship.locked != locked:
                logger.error(u'Failed to {} the ship {} ().'.format(
                    'lock' if locked else 'unlock', ship.name))
                return
        self.screen.unfocus_ship_selection()


class LockUniqueShips(base.Manipulator):

    @staticmethod
    def get_unlocked_unique_ship_ids(ship_list):
        ship_ids = []
        for ship in ship_list.ships.itervalues():
            if not ship.locked and ship.unique:
                ship_ids.append(ship.id)
        return ship_ids

    def run(self):
        self.require_objects(['ShipList'])
        ship_list = self.objects['ShipList']
        ship_ids = LockUniqueShips.get_unlocked_unique_ship_ids(ship_list)
        if ship_ids:
            yield self.do_manipulator(LockShips, ship_ids=ship_ids,
                                      locked=True)


class AutoLockUniqueShips(base.AutoManipulator):

    @classmethod
    def monitored_objects(cls):
        return ['ShipList']

    @classmethod
    def can_trigger(cls, owner):
        if owner.screen_id != screens.PORT_MAIN:
            return
        ship_list = owner.objects['ShipList']
        if LockUniqueShips.get_unlocked_unique_ship_ids(ship_list):
            return {}

    def run(self):
        yield self.do_manipulator(LockUniqueShips)


class FormCombinedFleet(base.Manipulator):

    def run(self, fleet_type):
        fleet_type = int(fleet_type)
        fleet_list = self.objects['FleetList']
        if fleet_list.combined_fleet_type == fleet_type:
            logger.info('Fleets is already in the desired combined type.')
            return
        fleet_type_index = {
            kcsapi.FleetList.COMBINED_FLEET_TYPE_MOBILE: 0,
            kcsapi.FleetList.COMBINED_FLEET_TYPE_SURFACE: 1,
        }[fleet_type]
        logger.info('Trying to form a combined fleet.')
        if len(fleet_list.fleets) < 2 or fleet_list.fleets[1].mission_id:
            raise Exception('Fleet 2 is not available.')
        yield self.screen.change_screen(screens.PORT_ORGANIZING)
        yield self.screen.select_fleet(2)
        if fleet_list.combined:
            yield self.screen.dissolve_combined_fleet()
        yield self.screen.form_combined_fleet(fleet_type_index)


class MarkReservedForUse(base.Manipulator):

    def run(self, ship_ids, reserved_for_use):
        ship_list = self.objects['ShipList']
        for ship_id in ship_ids:
            ship = ship_list.ships[str(ship_id)]
            if ship.reserved_for_use == reserved_for_use:
                continue
            logger.debug(
                u'Marking ship {} ({}) reserved for use: {} -> {}'.format(
                    ship.name, ship.id, ship.reserved_for_use,
                    reserved_for_use))
            ship.reserved_for_use = reserved_for_use
        yield 0.0


class AutoUnmarkReservedForUse(base.AutoManipulator):

    @classmethod
    def monitored_objects(cls):
        return ['ShipList']

    @classmethod
    def run_only_when_idle(cls):
        return True

    @classmethod
    def can_trigger(cls, owner):
        if screens.in_category(owner.screen_id, screens.PORT_MAIN):
            return
        ship_list = owner.objects['ShipList']
        if any([s.reserved_for_use for s in ship_list.ships.itervalues()]):
            return {}

    def run(self):
        ship_list = self.objects['ShipList']
        yield self.do_manipulator(
            MarkReservedForUse,
            ship_ids=[s.id for s in ship_list.ships.itervalues() if
                      s.reserved_for_use],
            reserved_for_use=False)
