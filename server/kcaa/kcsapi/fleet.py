#!/usr/bin/env python

import logging

import jsonobject
import model
import ship


logger = logging.getLogger('kcaa.kcsapi.fleet')


class Fleet(jsonobject.JSONSerializableObject):

    id = jsonobject.ReadonlyJSONProperty('id', value_type=int)
    """ID."""
    name = jsonobject.ReadonlyJSONProperty('name', value_type=unicode)
    """Name."""
    ship_ids = jsonobject.JSONProperty('ship_ids', value_type=list,
                                       element_type=int)
    """IDs of ships belonging to this fleet."""
    mission_id = jsonobject.JSONProperty('mission_id', value_type=int)
    """ID of mission which this fleet is undertaking."""
    mission_complete = jsonobject.JSONProperty('mission_complete',
                                               value_type=bool)
    """True if the mission is complete. Updated when the screen transitioned to
    PORT_MAIN."""


class FleetList(model.KCAAObject):
    """List of fleets (decks)."""

    fleets = jsonobject.JSONProperty('fleets', [], value_type=list,
                                     element_type=Fleet)
    """Fleets.

    Note that this list has 0-origin, while other objects use 1-origin index to
    reference a fleet."""

    def find_fleet_for_ship(self, ship_id):
        for fleet in self.fleets:
            if ship_id in fleet.ship_ids:
                return fleet
        return None

    def update(self, api_name, request, response, objects, debug):
        super(FleetList, self).update(api_name, request, response, objects,
                                      debug)
        ship_list = objects.get('ShipList')
        if api_name == '/api_port/port':
            self.update_fleets(response.api_data.api_deck_port, ship_list)
        elif api_name == '/api_get_member/deck':
            self.update_fleets(response.api_data, ship_list)
        elif api_name == '/api_get_member/ship3':
            self.update_fleets(response.api_data.api_deck_data, ship_list)
        elif api_name == '/api_req_hensei/change':
            fleet = self.fleets[int(request.api_id)-1]
            ship_index = int(request.api_ship_idx)
            ship_id = int(request.api_ship_id)
            if ship_id == -1:
                # -1 means the ship was removed from the fleet.
                del fleet.ship_ids[ship_index]
            elif ship_id == -2:
                # -2 means all the ships except the flag ship were removed.
                del fleet.ship_ids[1:]
            elif ship_index >= len(fleet.ship_ids):
                fleet.ship_ids.append(ship_id)
            else:
                # First swap the ship if any.
                for another_fleet in self.fleets:
                    try:
                        old_index = another_fleet.ship_ids.index(ship_id)
                        another_fleet.ship_ids[old_index] = (
                            fleet.ship_ids[ship_index])
                        break
                    except ValueError:
                        pass
                fleet.ship_ids[ship_index] = ship_id

    def update_fleets(self, fleet_data, ship_list):
        self.fleets = []
        for data in fleet_data:
            mission_id = None
            mission_complete = None
            if data.api_mission[0] != 0:
                mission_id = data.api_mission[1]
                # TODO: Fix this. This is not accurate.
                # Probably better to use Mission's eta and the current
                # time?
                mission_complete = data.api_mission[3] == 1
            self.fleets.append(Fleet(
                id=data.api_id,
                name=data.api_name,
                ship_ids=filter(lambda x: x != -1, data.api_ship),
                mission_id=mission_id,
                mission_complete=mission_complete))
        # Update Ship.away_for_mission.
        # TODO: Consider doing this in ShipList. However that will require the
        # dependency order to be FleetList -> ShipList.
        # TODO: Properly test this.
        if not ship_list:
            return
        ship_ids_away_for_mission = set()
        for fleet in self.fleets:
            if not fleet.mission_id:
                continue
            for ship_id in fleet.ship_ids:
                ship_ids_away_for_mission.add(ship_id)
        for s in ship_list.ships.itervalues():
            s.away_for_mission = s.id in ship_ids_away_for_mission


class FleetDeployment(jsonobject.JSONSerializableObject):

    name = jsonobject.JSONProperty('name', value_type=unicode)
    """Name of the fleet."""
    global_predicate = jsonobject.JSONProperty(
        'global_predicate', value_type=ship.ShipPredicate)
    """Global predicate applied to all of ship selections.

    A global predicate is applied as AND operator for all ship selections
    defined here. This is usually used for selecting only available ships (no
    repair, no mission and not fatal etc.).
    """
    ship_requirements = jsonobject.JSONProperty(
        'ship_requirements', [], value_type=list,
        element_type=ship.ShipRequirement)
    """Ship requirements."""

    def get_ships(self, ship_list):
        # TODO: Unit test.
        ship_pool = ship_list.ships.values()
        if self.global_predicate:
            ship_pool = [s for s in ship_pool if
                         self.global_predicate.apply(s)]
        ships = []
        for ship_requirement in self.ship_requirements:
            predicate = ship_requirement.predicate
            applicable_ships = [s for s in ship_pool if predicate.apply(s)]
            ship_requirement.sorter.sort(applicable_ships)
            if not applicable_ships:
                if not ship_requirement.omittable:
                    ships.append(ship.Ship(id=-1))
                else:
                    ships.append(ship.Ship(id=0))
            else:
                ships.append(applicable_ships[0])
                ship_pool.remove(applicable_ships[0])
        return [s for s in ships if s]


class SavedFleetDeploymentShipIdList(ship.ShipIdList):

    @property
    def required_objects(self):
        return ['ShipList', 'Preferences']

    def request(self, objects, fleet_name):
        super(SavedFleetDeploymentShipIdList, self).request(objects)
        unicode_fleet_name = fleet_name.decode('utf8')
        preferences = objects['Preferences']
        matching_fleets = [sf for sf in preferences.fleet_prefs.saved_fleets
                           if sf.name == unicode_fleet_name]
        if not matching_fleets:
            logger.error('Saved fleet {} is not found.'.format(
                fleet_name))
            return None
        fleet_deployment = matching_fleets[0]
        ship_list = objects['ShipList']
        ships = fleet_deployment.get_ships(ship_list)
        self.ship_ids = [ship.id for ship in ships]
        return self


class FleetDeploymentShipIdList(ship.ShipIdList):

    @property
    def required_objects(self):
        return ['ShipList']

    def request(self, objects, fleet_deployment):
        super(FleetDeploymentShipIdList, self).request(objects)
        fleet_deployment = FleetDeployment.parse_text(fleet_deployment)
        ship_list = objects['ShipList']
        ships = fleet_deployment.get_ships(ship_list)
        self.ship_ids = [ship.id for ship in ships]
        return self
