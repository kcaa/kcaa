#!/usr/bin/env python

import logging

import base
from kcaa import screens


logger = logging.getLogger('kcaa.manipulators.shipyard')


class BuildShip(base.Manipulator):

    def run(self, fuel, ammo, steel, bauxite, grand, material):
        fuel = int(fuel)
        ammo = int(ammo)
        steel = int(steel)
        bauxite = int(bauxite)
        grand = grand is True or grand == 'true'
        material = int(material)
        logger.info('Buliding a {} ship with [{}, {}, {}, {}]'.format(
            'grand' if grand else 'normal', fuel, ammo, steel, bauxite))
        # TODO: Check if there is room for building.
        if grand:
            if (fuel < 1500 or fuel > 7000 or fuel % 10 != 0 or
                    ammo < 1500 or ammo > 7000 or ammo % 10 != 0 or
                    steel < 2000 or steel > 7000 or steel % 10 != 0 or
                    bauxite < 1000 or bauxite > 7000 or bauxite % 10 != 0 or
                    material not in (1, 20, 100)):
                logger.error('Resource amount is invalid for grand building.')
                return
        else:
            if (fuel < 30 or fuel >= 1000 or
                    ammo < 30 or ammo >= 1000 or
                    steel < 30 or steel >= 1000 or
                    bauxite < 30 or bauxite >= 1000):
                logger.error('Resource amount is invalid for normal building.')
                return
        # TODO: Select an empty slot.
        slot_id = 0
        yield self.screen.change_screen(screens.PORT_SHIPYARD)
        yield self.screen.select_slot(slot_id)
        if grand:
            yield self.screen.try_grand_building()
            yield self.screen.set_material(material)
        yield self.screen.set_resource(grand, fuel, ammo, steel, bauxite)
        yield self.screen.confirm_building()
