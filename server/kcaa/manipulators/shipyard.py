#!/usr/bin/env python

import logging
import time

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
        build_dock = self.objects.get('BuildDock')
        if not build_dock:
            logger.error('No build dock was found. Giving up.')
            return
        empty_slots = build_dock.empty_slots
        if not empty_slots:
            logger.error('No empty build slot was found.')
            return
        slot_id = empty_slots[0].id - 1
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
        yield self.screen.change_screen(screens.PORT_SHIPYARD)
        yield self.screen.select_slot(slot_id)
        if grand:
            yield self.screen.try_grand_building()
            yield self.screen.set_material(material)
        yield self.screen.set_resource(grand, fuel, ammo, steel, bauxite)
        yield self.screen.confirm_building()


class ReceiveShip(base.Manipulator):

    def run(self, slot_id):
        slot_id = int(slot_id)
        yield self.screen.change_screen(screens.PORT_SHIPYARD)
        yield self.screen.select_slot(slot_id - 1)
        yield self.screen.check_ship()


class AutoReceiveShips(base.AutoManipulator):

    # Ship buliding are completed on time? At least there is no harm on
    # checking the completion when the reported ETA has come.
    precursor_duration = 0

    @classmethod
    def required_objects(cls):
        return ['BuildDock']

    @classmethod
    def can_trigger(cls, owner):
        if not screens.in_category(owner.screen_id, screens.PORT):
            return
        build_dock = owner.objects.get('BuildDock')
        now = long(1000 * time.time()) + cls.precursor_duration
        slot_ids = []
        for slot in build_dock.slots:
            if slot.completed(now):
                slot_ids.append(slot.id)
        if slot_ids:
            return {'slot_ids': slot_ids}

    def run(self, slot_ids):
        yield 1.0
        for slot_id in slot_ids:
            yield self.do_manipulator(ReceiveShip, slot_id=slot_id)


class DevelopEquipment(base.Manipulator):

    def run(self, fuel, ammo, steel, bauxite):
        fuel = int(fuel)
        ammo = int(ammo)
        steel = int(steel)
        bauxite = int(bauxite)
        logger.info('Developing an equipment with [{}, {}, {}, {}]'.format(
            fuel, ammo, steel, bauxite))
        if (fuel < 10 or fuel > 300 or
                ammo < 10 or ammo > 300 or
                steel < 10 or steel > 300 or
                bauxite < 10 or bauxite > 300):
            logger.error('Resource amount is invalid for development.')
            return
        yield self.screen.change_screen(screens.PORT_SHIPYARD)
        yield self.screen.try_equipment_development()
        yield self.screen.set_development_resource(fuel, ammo, steel, bauxite)
        yield self.screen.confirm_development()
        yield self.screen.check_equipment()
