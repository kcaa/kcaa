#!/usr/bin/env python

import pytest

import practice
import ship


class TestPractice(object):

    def get_ship_entries(self, ship_types):
        return map(lambda ship_type: practice.ShipEntry(ship_type=ship_type),
                   ship_types)

    def test_get_fleet_type_submarines(self):
        ships = self.get_ship_entries([
            ship.ShipDefinition.SHIP_TYPE_SUBMARINE])
        assert (practice.Practice.get_fleet_type(ships) ==
                practice.Practice.FLEET_TYPE_SUBMARINES)
        ships = self.get_ship_entries([
            ship.ShipDefinition.SHIP_TYPE_SUBMARINE_AIRCRAFT_CARRIER,
            ship.ShipDefinition.SHIP_TYPE_SUBMARINE])
        assert (practice.Practice.get_fleet_type(ships) ==
                practice.Practice.FLEET_TYPE_SUBMARINES)
        ships = self.get_ship_entries([
            ship.ShipDefinition.SHIP_TYPE_SUBMARINE,
            ship.ShipDefinition.SHIP_TYPE_DESTROYER,
            ship.ShipDefinition.SHIP_TYPE_DESTROYER,
            ship.ShipDefinition.SHIP_TYPE_DESTROYER])
        assert (practice.Practice.get_fleet_type(ships) ==
                practice.Practice.FLEET_TYPE_SUBMARINES)
        ships = self.get_ship_entries([
            ship.ShipDefinition.SHIP_TYPE_DESTROYER,
            ship.ShipDefinition.SHIP_TYPE_DESTROYER,
            ship.ShipDefinition.SHIP_TYPE_SUBMARINE,
            ship.ShipDefinition.SHIP_TYPE_SUBMARINE,
            ship.ShipDefinition.SHIP_TYPE_SUBMARINE])
        assert (practice.Practice.get_fleet_type(ships) ==
                practice.Practice.FLEET_TYPE_SUBMARINES)
        ships = self.get_ship_entries([
            ship.ShipDefinition.SHIP_TYPE_DESTROYER,
            ship.ShipDefinition.SHIP_TYPE_DESTROYER,
            ship.ShipDefinition.SHIP_TYPE_DESTROYER,
            ship.ShipDefinition.SHIP_TYPE_SUBMARINE,
            ship.ShipDefinition.SHIP_TYPE_SUBMARINE,
            ship.ShipDefinition.SHIP_TYPE_SUBMARINE])
        assert (practice.Practice.get_fleet_type(ships) !=
                practice.Practice.FLEET_TYPE_SUBMARINES)

    def test_get_fleet_type_no_anti_submarine(self):
        ships = self.get_ship_entries([
            ship.ShipDefinition.SHIP_TYPE_BATTLESHIP,
            ship.ShipDefinition.SHIP_TYPE_BATTLESHIP,
            ship.ShipDefinition.SHIP_TYPE_HEAVY_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_AIRCRAFT_CARRIER,
            ship.ShipDefinition.SHIP_TYPE_AIRCRAFT_CARRIER,
            ship.ShipDefinition.SHIP_TYPE_SEAPLANE_TENDER])
        assert (practice.Practice.get_fleet_type(ships) ==
                practice.Practice.FLEET_TYPE_NO_ANTI_SUBMARINE)
        ships = self.get_ship_entries([
            ship.ShipDefinition.SHIP_TYPE_BATTLESHIP,
            ship.ShipDefinition.SHIP_TYPE_BATTLESHIP,
            ship.ShipDefinition.SHIP_TYPE_AIRCRAFT_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_AIRCRAFT_CARRIER,
            ship.ShipDefinition.SHIP_TYPE_AIRCRAFT_CARRIER,
            ship.ShipDefinition.SHIP_TYPE_SEAPLANE_TENDER])
        assert (practice.Practice.get_fleet_type(ships) !=
                practice.Practice.FLEET_TYPE_NO_ANTI_SUBMARINE)

    def test_get_fleet_type_aircraft_carriers(self):
        ships = self.get_ship_entries([
            ship.ShipDefinition.SHIP_TYPE_AIRCRAFT_CARRIER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_AIRCRAFT_CARRIER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_AIRCRAFT_CARRIER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER])
        assert (practice.Practice.get_fleet_type(ships) ==
                practice.Practice.FLEET_TYPE_AIRCRAFT_CARRIERS)

    def test_get_fleet_type_battleships(self):
        ships = self.get_ship_entries([
            ship.ShipDefinition.SHIP_TYPE_BATTLESHIP,
            ship.ShipDefinition.SHIP_TYPE_BATTLESHIP,
            ship.ShipDefinition.SHIP_TYPE_BATTLESHIP,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER])
        assert (practice.Practice.get_fleet_type(ships) ==
                practice.Practice.FLEET_TYPE_BATTLESHIPS)
        ships = self.get_ship_entries([
            ship.ShipDefinition.SHIP_TYPE_BATTLESHIP,
            ship.ShipDefinition.SHIP_TYPE_BATTLESHIP,
            ship.ShipDefinition.SHIP_TYPE_AIRCRAFT_CARRIER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER])
        assert (practice.Practice.get_fleet_type(ships) ==
                practice.Practice.FLEET_TYPE_BATTLESHIPS)

    def test_get_fleet_type_heavy_cruisers(self):
        ships = self.get_ship_entries([
            ship.ShipDefinition.SHIP_TYPE_HEAVY_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_HEAVY_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_AIRCRAFT_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER])
        assert (practice.Practice.get_fleet_type(ships) ==
                practice.Practice.FLEET_TYPE_HEAVY_CRUISERS)
        ships = self.get_ship_entries([
            ship.ShipDefinition.SHIP_TYPE_HEAVY_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_AIRCRAFT_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_AIRCRAFT_CARRIER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER])
        assert (practice.Practice.get_fleet_type(ships) ==
                practice.Practice.FLEET_TYPE_HEAVY_CRUISERS)

    def test_get_fleet_type_light_cruisers(self):
        ships = self.get_ship_entries([
            ship.ShipDefinition.SHIP_TYPE_TORPEDO_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_DESTROYER,
            ship.ShipDefinition.SHIP_TYPE_SUBMARINE])
        assert (practice.Practice.get_fleet_type(ships) ==
                practice.Practice.FLEET_TYPE_LIGHT_CRUISERS)
        ships = self.get_ship_entries([
            ship.ShipDefinition.SHIP_TYPE_TORPEDO_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_DESTROYER,
            ship.ShipDefinition.SHIP_TYPE_DESTROYER,
            ship.ShipDefinition.SHIP_TYPE_SUBMARINE])
        assert (practice.Practice.get_fleet_type(ships) !=
                practice.Practice.FLEET_TYPE_LIGHT_CRUISERS)

    def test_get_fleet_type_destroyers(self):
        ships = self.get_ship_entries([
            ship.ShipDefinition.SHIP_TYPE_DESTROYER,
            ship.ShipDefinition.SHIP_TYPE_DESTROYER,
            ship.ShipDefinition.SHIP_TYPE_DESTROYER,
            ship.ShipDefinition.SHIP_TYPE_SUBMARINE,
            ship.ShipDefinition.SHIP_TYPE_SUBMARINE])
        assert (practice.Practice.get_fleet_type(ships) ==
                practice.Practice.FLEET_TYPE_DESTROYERS)
        ships = self.get_ship_entries([
            ship.ShipDefinition.SHIP_TYPE_DESTROYER,
            ship.ShipDefinition.SHIP_TYPE_DESTROYER,
            ship.ShipDefinition.SHIP_TYPE_DESTROYER,
            ship.ShipDefinition.SHIP_TYPE_SUBMARINE,
            ship.ShipDefinition.SHIP_TYPE_SUBMARINE,
            ship.ShipDefinition.SHIP_TYPE_SUBMARINE])
        assert (practice.Practice.get_fleet_type(ships) !=
                practice.Practice.FLEET_TYPE_DESTROYERS)

    def test_get_fleet_type_generic(self):
        ships = self.get_ship_entries([
            ship.ShipDefinition.SHIP_TYPE_BATTLESHIP,
            ship.ShipDefinition.SHIP_TYPE_AIRCRAFT_CARRIER,
            ship.ShipDefinition.SHIP_TYPE_HEAVY_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_LIGHT_CRUISER,
            ship.ShipDefinition.SHIP_TYPE_DESTROYER])
        assert (practice.Practice.get_fleet_type(ships) ==
                practice.Practice.FLEET_TYPE_GENERIC)


def main():
    import doctest
    doctest.testmod(practice)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
