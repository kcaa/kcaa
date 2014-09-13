#!/usr/bin/env python

import pytest

import jsonobject
import repair
import ship


class TestRepairDock(object):

    def pytest_funcarg__repair_dock(self):
        return repair.RepairDock(slots=[
            repair.RepairSlot(id=1, ship_id=100, eta=123),
            repair.RepairSlot(id=2, ship_id=0, eta=0)])

    def pytest_funcarg__ship_list(self):
        return ship.ShipList(ships={
            '100': ship.Ship(
                id=100,
                hitpoint=ship.Variable(
                    current=12,
                    maximum=34)),
            '101': ship.Ship(
                id=101,
                hitpoint=ship.Variable(
                    current=56,
                    maximum=78))})

    def test_update_repair_start(self, repair_dock, ship_list):
        request = jsonobject.parse_text("""{
            "api_ndock_id": "2",
            "api_ship_id": "101",
            "api_highspeed": "0"
        }""")
        objects = {'ShipList': ship_list}
        repair_dock.update(
            '/api_req_nyukyo/start', request, None, objects, False)
        assert repair_dock.slots[1].ship_id == 101
        assert ship_list.ships['101'].hitpoint.current == 56

    def test_update_repair_start_highspeed(self, repair_dock, ship_list):
        request = jsonobject.parse_text("""{
            "api_ndock_id": "2",
            "api_ship_id": "101",
            "api_highspeed": "1"
        }""")
        objects = {'ShipList': ship_list}
        repair_dock.update(
            '/api_req_nyukyo/start', request, None, objects, False)
        assert repair_dock.slots[1].ship_id == 0
        ship_101 = ship_list.ships['101']
        assert ship_101.hitpoint.current == ship_101.hitpoint.maximum

    def test_update_repair_speedchange(self, repair_dock, ship_list):
        request = jsonobject.parse_text("""{
            "api_ndock_id": "1"
        }""")
        objects = {'ShipList': ship_list}
        repair_dock.update(
            '/api_req_nyukyo/speedchange', request, None, objects, False)
        assert repair_dock.slots[0].ship_id == 0
        assert repair_dock.slots[0].eta == 0L
        ship_100 = ship_list.ships['100']
        assert ship_100.hitpoint.current == ship_100.hitpoint.maximum


def main():
    import doctest
    doctest.testmod(repair)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
