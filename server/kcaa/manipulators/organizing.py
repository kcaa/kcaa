#!/usr/bin/env python

import logging

import base
from kcaa import screens


logger = logging.getLogger('kcaa.manipulators.organization')


class LoadFleet(base.Manipulator):

    def run(self, fleet_id, saved_fleet_name):
        fleet_id = int(fleet_id)
        unicode_saved_fleet_name = saved_fleet_name.decode('utf8')
        logger.info('Loading saved fleet {} to fleet {}'.format(
            saved_fleet_name, fleet_id))
        preferences = self.objects['Preferences']
        ship_list = self.objects.get('ShipList')
        if not ship_list:
            logger.info('No ship list was found. Giving up.')
            return
        matching_fleets = [sf for sf in preferences.fleet_prefs.saved_fleets
                           if sf.name == unicode_saved_fleet_name]
        if not matching_fleets:
            logger.error('No saved fleet named {} was found'.format(
                saved_fleet_name))
            return
        saved_fleet = matching_fleets[0]
        logger.debug(saved_fleet.json(ensure_ascii=False).encode('utf8'))
        # TODO: Ensure the sort mode is Lv in the Kancolle player?
        # TODO: Check if a ship belongs to a fleet which is in a mission.
        yield self.screen.change_screen(screens.PORT_ORGANIZING)
        yield self.screen.select_fleet(fleet_id)
        yield self.screen.detach_all_ships()
        for pos, ship_requirement in enumerate(saved_fleet.ship_requirements):
            page, index = ship_list.get_ship_position(ship_requirement.id)
            # Do I need to ensure the ship was properly changed?
            yield self.screen.change_member(pos)
            yield self.screen.select_page(page)
            yield self.screen.select_ship(index)
            yield self.screen.confirm()
