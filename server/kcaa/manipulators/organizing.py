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
        # Assuming the fleet object itself is not replaced from now on.
        # This may break when KCSAPI changes -- beware!
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
                logger.info(repr(fleet.ship_ids))
                return
        num_ships = len(ship_ids)
        # Remove unnecessary ships.
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
        preferences = self.manager.preferences
        matching_fleets = [sf for sf in preferences.fleet_prefs.saved_fleets
                           if sf.name == unicode_saved_fleet_name]
        if not matching_fleets:
            logger.error('No saved fleet named {} was found'.format(
                saved_fleet_name))
            return
        saved_fleet = matching_fleets[0]
        ship_ids = map(lambda sr: sr.id, saved_fleet.ship_requirements)
        yield self.do_manipulator(LoadShips, fleet_id, ship_ids)
