#!/usr/bin/env python

import logging

import base
from kcaa import screens


logger = logging.getLogger('kcaa.manipulators.logistics')


class FleetCharge(base.Manipulator):

    def run(self, fleet_id):
        logger.info('Charging fleet {}'.format(fleet_id))
        yield self.screen.change_screen(screens.PORT_LOGISTICS)


class AutoFleetCharge(base.AutoManipulator):

    @classmethod
    def can_trigger(cls, owner):
        if not screens.in_category(owner.screen_id, screens.PORT):
            return
        fleet_list = owner.objects.get('FleetList')
        if not fleet_list:
            return
        ship_list = owner.objects.get('ShipList')
        if not ship_list:
            return
        fleet_ids_to_charge = []
        for fleet in fleet_list.fleets:
            if fleet.mission_id:
                continue
            for ship_id in fleet.ship_ids:
                ship = ship_list.ships[str(ship_id)]
                loaded = ship.loaded_resource
                capacity = ship.resource_capacity
                if loaded.fuel < capacity.fuel or loaded.ammo < capacity.ammo:
                    fleet_ids_to_charge.append(fleet.id)
                    break
        if fleet_ids_to_charge:
            return {'fleet_ids': fleet_ids_to_charge}

    def run(self, fleet_ids):
        for fleet_id in fleet_ids:
            yield self.do_manipulator(FleetCharge, fleet_id)
