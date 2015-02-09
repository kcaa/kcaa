#!/usr/bin/env python

import logging

import base
from kcaa import screens


logger = logging.getLogger('kcaa.manipulators.logistics')


class ChargeFleet(base.Manipulator):

    def run(self, fleet_id):
        fleet_id = int(fleet_id)
        logger.info('Charging fleet {}'.format(fleet_id))
        ship_list = self.objects['ShipList']
        fleet_list = self.objects['FleetList']
        resource_full = True
        for ship_id in fleet_list.fleets[fleet_id - 1].ship_ids:
            ship = ship_list.ships[str(ship_id)]
            if not ship.resource_full:
                resource_full = False
                break
        if resource_full:
            logger.debug('Fleet {} is full of resources.'.format(fleet_id))
            return
        yield self.screen.change_screen(screens.PORT_LOGISTICS)
        yield self.screen.select_fleet(fleet_id)
        yield self.screen.select_all_members()
        yield self.screen.charge_both()


class AutoChargeFleet(base.AutoManipulator):

    @classmethod
    def monitored_objects(cls):
        return ['ShipList', 'FleetList']

    @classmethod
    def can_trigger(cls, owner):
        if not screens.in_category(owner.screen_id, screens.PORT):
            return
        fleet_list = owner.objects.get('FleetList')
        ship_list = owner.objects.get('ShipList')
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
        yield 1.0
        for fleet_id in fleet_ids:
            yield self.do_manipulator(ChargeFleet, fleet_id)
