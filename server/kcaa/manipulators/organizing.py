#!/usr/bin/env python

import logging

import base
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
        if ship_ids == fleet.ship_ids:
            logger.info('All ships are already standing by.')
            return
        # TODO: Ensure the sort mode is Lv in the Kancolle player?
        # TODO: Check if a ship belongs to a fleet which is in a mission.
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
        unicode_saved_fleet_name = saved_fleet_name.decode('utf8')
        logger.info('Loading saved fleet {} to fleet {}'.format(
            saved_fleet_name, fleet_id))
        ship_list = self.objects.get('ShipList')
        if not ship_list:
            logger.error('No ship list was found. Giving up.')
            return
        fleet_list = self.objects.get('FleetList')
        if not fleet_list:
            logger.error('No fleet list was found. Giving up.')
            return
        # TODO: Just request SavedFleetShips.
        preferences = self.manager.preferences
        matching_fleets = [sf for sf in preferences.fleet_prefs.saved_fleets
                           if sf.name == unicode_saved_fleet_name]
        if not matching_fleets:
            logger.error('No saved fleet named {} was found'.format(
                saved_fleet_name))
            return
        saved_fleet = matching_fleets[0]
        ships = saved_fleet.get_ships(ship_list)
        if not ships:
            logger.error('Saved fleet {} cannot be loaded.'.format(
                saved_fleet_name))
            return
        ship_ids = [ship.id for ship in ships]
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
                logger.error('Failed to {} the ship {} ().'.format(
                    'lock' if locked else 'unlock', ship.name.encode('utf8')))
                return
        self.screen.unfocus_ship_selection()


class AutoLockUniqueShips(base.AutoManipulator):

    @classmethod
    def can_trigger(cls, owner):
        if not screens.in_category(owner.screen_id, screens.PORT):
            return
        ship_list = owner.objects.get('ShipList')
        if not ship_list:
            return
        ship_ids_to_lock = []
        for ship in ship_list.ships.itervalues():
            if not ship.locked and ship_list.is_unique(ship):
                ship_ids_to_lock.append(ship.id)
        if ship_ids_to_lock:
            return {'ship_ids': ship_ids_to_lock}

    def run(self, ship_ids):
        yield 1.0
        yield self.do_manipulator(LockShips, ship_ids, True)
