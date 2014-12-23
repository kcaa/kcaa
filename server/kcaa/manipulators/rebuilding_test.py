#!/usr/bin/env python

import pytest

import rebuilding
from kcaa import kcsapi


class TestReplaceEquipments(object):

    def pytest_funcarg__ship_def_list(self):
        return kcsapi.ShipDefinitionList(ship_types={
            '10000': kcsapi.ShipTypeDefinition(
                id=10000,
                name=u'Ship type 10000',
                loadable_equipment_types=[True, False])})

    def pytest_funcarg__ship_list(self):
        return kcsapi.ShipList(ships={
            '1': kcsapi.Ship(
                id=1,
                ship_type=10000,
                equipment_ids=[-1, -1]),
            '2': kcsapi.Ship(
                id=2,
                ship_type=10000,
                equipment_ids=[100, 101, -1])})

    def pytest_funcarg__equipment_list(self):
        return kcsapi.EquipmentList(
            items={
                '100': kcsapi.Equipment(id=100, item_id=1),
                '101': kcsapi.Equipment(id=101, item_id=1),
                '102': kcsapi.Equipment(id=102, item_id=1),
                '200': kcsapi.Equipment(id=200, item_id=2)},
            item_instances={
                '1': kcsapi.EquipmentIdList(item_ids=[100, 101, 102]),
                '2': kcsapi.EquipmentIdList(item_ids=[200])})

    def test_select_equipment_ids_different_length(
            self, ship_def_list, ship_list, equipment_list):
        ship = ship_list.ships['1']
        equipment_defs = [
            kcsapi.EquipmentDefinition(id=1, name=u'1')]
        assert rebuilding.ReplaceEquipments.select_equipment_ids(
            ship, equipment_defs, ship_def_list, ship_list,
            equipment_list) is None

    def test_select_equipment_ids_non_empty_slot_after_empty_slots(
            self, ship_def_list, ship_list, equipment_list):
        ship = ship_list.ships['1']
        equipment_defs = [
            None,
            kcsapi.EquipmentDefinition(id=1, name=u'1')]
        assert rebuilding.ReplaceEquipments.select_equipment_ids(
            ship, equipment_defs, ship_def_list, ship_list,
            equipment_list) is None

    def test_select_equipment_ids_no_avialable_unequipped(
            self, ship_def_list, ship_list, equipment_list):
        ship = ship_list.ships['1']
        equipment_defs = [
            kcsapi.EquipmentDefinition(id=1, name=u'1'),
            kcsapi.EquipmentDefinition(id=1, name=u'1')]
        assert rebuilding.ReplaceEquipments.select_equipment_ids(
            ship, equipment_defs, ship_def_list, ship_list,
            equipment_list) is None

    def test_select_equipment_ids_no_avialable_at_all(
            self, ship_def_list, ship_list, equipment_list):
        ship = ship_list.ships['1']
        equipment_defs = [
            kcsapi.EquipmentDefinition(id=9999, name=u'1'),
            None]
        assert rebuilding.ReplaceEquipments.select_equipment_ids(
            ship, equipment_defs, ship_def_list, ship_list,
            equipment_list) is None

    def test_select_equipment_ids_same_definitions(
            self, ship_def_list, ship_list, equipment_list):
        ship = ship_list.ships['2']
        equipment_defs = [
            kcsapi.EquipmentDefinition(id=1, name=u'1'),
            kcsapi.EquipmentDefinition(id=1, name=u'1'),
            None]
        assert rebuilding.ReplaceEquipments.select_equipment_ids(
            ship, equipment_defs, ship_def_list, ship_list,
            equipment_list) == [100, 101, -1]

    def test_select_equipment_ids_unloadable_types(
            self, ship_def_list, ship_list, equipment_list):
        ship = ship_list.ships['1']
        equipment_defs = [
            kcsapi.EquipmentDefinition(id=2, name=u'2'),
            None]
        assert rebuilding.ReplaceEquipments.select_equipment_ids(
            ship, equipment_defs, ship_def_list, ship_list,
            equipment_list) is None

    def test_select_equipment_ids_loadable_types(
            self, ship_def_list, ship_list, equipment_list):
        ship = ship_list.ships['1']
        equipment_defs = [
            kcsapi.EquipmentDefinition(id=1, name=u'1'),
            None]
        assert rebuilding.ReplaceEquipments.select_equipment_ids(
            ship, equipment_defs, ship_def_list, ship_list,
            equipment_list) == [102, -1]


def main():
    import doctest
    doctest.testmod(rebuilding)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
