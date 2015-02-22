#!/usr/bin/env python

import logging

import base
import kcaa
from kcaa import screens


logger = logging.getLogger('kcaa.manipulators.organization')


class LoadShips(base.Manipulator):
    """Load the given ships to the fleet."""

    def run(self, fleet_id, ship_ids):
        fleet_id = int(fleet_id)
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
            logger.error('Some ships are missing.')
            return
        if any([s.away_for_mission for s in ships]):
            logger.error('Some ships are away for mission.')
            return
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
            # Desired ships is already present; skipping.
            if (pos < num_ships_in_fleet and
                    fleet.ship_ids[pos] == ship_id):
                continue
            page, index = ship_list.get_ship_position(ship_id)
            yield self.screen.change_member(pos)
            yield self.screen.select_page(page, ship_list.max_page)
            yield self.screen.select_ship(index)
            yield self.screen.confirm()
            if fleet.ship_ids[pos] != ship_id:
                logger.error(
                    'Failed to change the ship to {}. Currently you have {}.'
                    .format(ship_id, fleet.ship_ids[pos]))
                logger.debug(repr(fleet.ship_ids))
                return
        num_ships = len(ship_ids)
        # Remove unnecessary ships.
        if num_ships == 1:
            yield self.screen.detach_all_ships()
        else:
            for _ in xrange(num_ships_in_fleet - num_ships):
                yield self.screen.change_member(num_ships)
                yield self.screen.select_ship(-1)


class LoadFleet(base.Manipulator):

    def run(self, fleet_id, saved_fleet_name):
        fleet_id = int(fleet_id)
        unicode_fleet_name = saved_fleet_name.decode('utf8')
        logger.info('Loading saved fleet {} to fleet {}'.format(
            saved_fleet_name, fleet_id))
        ship_list = self.objects.get('ShipList')
        if not ship_list:
            logger.error('No ship list was found. Giving up.')
            return
        matching_fleets = [
            sf for sf in self.manager.preferences.fleet_prefs.saved_fleets
            if sf.name == unicode_fleet_name]
        if not matching_fleets:
            return
        fleet_deployment = matching_fleets[0]
        ships = [s for s in fleet_deployment.get_ships(ship_list) if
                 s.id != 0]
        if any([s.id < 0 for s in ships]):
            logger.error('Saved fleet {} has missing ships.'.format(
                saved_fleet_name))
            return
        if any([s.away_for_mission for s in ships]):
            logger.error('Saved fleet {} has a ship away for mission.'.format(
                saved_fleet_name))
            return
        ship_ids = [s.id for s in ships]
        yield self.do_manipulator(LoadShips, fleet_id, ship_ids)


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
        fleet_type_index = {
            kcaa.FleetList.COMBINED_FLEET_TYPE_MOBILE: 0,
            kcaa.FleetList.COMBINED_FLEET_TYPE_SURFACE: 1,
        }[fleet_type]
        logger.info('Trying to form a combined fleet.')
        fleet_list = self.objects['FleetList']
        if len(fleet_list.fleets) < 2 or fleet_list.fleets[1].mission_id:
            raise Exception('Fleet 2 is not available.')
        yield self.screen.change_screen(screens.PORT_ORGANIZING)
        yield self.screen.select_fleet(2)
        yield self.screen.dissolve_combined_fleet()
        yield self.screen.form_combined_fleet(fleet_type_index)
