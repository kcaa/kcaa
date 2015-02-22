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
        elif api_name == '/api_req_mission/start':
            fleet = self.fleets[int(request.api_deck_id) - 1]
            fleet.mission_id = int(request.api_mission_id)
            self.update_ship_away_for_mission(ship_list)

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
        self.update_ship_away_for_mission(ship_list)

    def update_ship_away_for_mission(self, ship_list):
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

    def get_ships(self, ship_pool):
        # TODO: Unit test.
        ship_pool = list(ship_pool)[:]
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
        return ships

    def are_all_ships_ready(self, ship_list):
        return all(s.id == 0 or s.ready for s in
                   self.get_ships(ship_list.ships.itervalues()))


class SavedFleetDeploymentShipIdList(ship.ShipIdList):

    @property
    def required_objects(self):
        return ['ShipList', 'Preferences']

    def request(self, fleet_name, ship_list, preferences):
        unicode_fleet_name = fleet_name.decode('utf8')
        matching_fleets = [sf for sf in preferences.fleet_prefs.saved_fleets
                           if sf.name == unicode_fleet_name]
        if not matching_fleets:
            logger.error('Saved fleet {} is not found.'.format(
                fleet_name))
            return None
        fleet_deployment = matching_fleets[0]
        ships = fleet_deployment.get_ships(ship_list.ships.itervalues())
        self.ship_ids = [ship.id for ship in ships]
        return self


class FleetDeploymentShipIdList(ship.ShipIdList):

    @property
    def required_objects(self):
        return ['ShipList']

    def request(self, fleet_deployment, ship_list):
        fleet_deployment = FleetDeployment.parse_text(fleet_deployment)
        ships = fleet_deployment.get_ships(ship_list.ships.itervalues())
        self.ship_ids = [ship.id for ship in ships]
        return self


class CombinedFleetDeployment(jsonobject.JSONSerializableObject):

    name = jsonobject.JSONProperty('name', value_type=unicode)
    """Name of the combined fleet."""
    primary_fleet_name = jsonobject.JSONProperty('primary_fleet_name',
                                                 value_type=unicode)
    """Name of the primary fleet."""
    secondary_fleet_name = jsonobject.JSONProperty('secondary_fleet_name',
                                                   value_type=unicode)
    """Name of the secondary fleet. Can be null if this combined fleet consists
    of a single fleet."""
    combined_fleet_type = jsonobject.JSONProperty('combined_fleet_type',
                                                  value_type=int)
    """Type of the combined fleet."""
    COMBINED_FLEET_TYPE_SINGLE = 0
    # Single fleet.
    COMBINED_FLEET_TYPE_MOBILE = 1
    # Mobile fleet, with plenty of aircraft carriers.
    COMBINED_FLEET_TYPE_SURFACE = 2
    # Surface ship fleet, a usual fleet with battleships or cruisers.
    escoting_fleet_name = jsonobject.JSONProperty('escoting_fleet_name',
                                                  value_type=unicode)
    """Name of the fleet escoting the primary fleet the whole way before the
    boss fleet. Can be null if no fleet is needed."""
    supporting_fleet_name = jsonobject.JSONProperty('supporting_fleet_name',
                                                    value_type=unicode)
    """Name of the fleet supporting the primary fleet in the battle against the
    boss fleet. Can be null if no fleet is needed."""


class CombinedFleetDeploymentShipIdList(model.KCAARequestableObject):

    primary_ship_ids = jsonobject.JSONProperty(
        'primary_ship_ids', value_type=list, element_type=int)
    """IDs of ships in the primary fleet."""
    secondary_ship_ids = jsonobject.JSONProperty(
        'secondary_ship_ids', value_type=list, element_type=int)
    """IDs of ships in the secondary fleet."""
    escoting_ship_ids = jsonobject.JSONProperty(
        'escoting_ship_ids', value_type=list, element_type=int)
    """IDs of ships in the escoting fleet."""
    supporting_ship_ids = jsonobject.JSONProperty(
        'supporting_ship_ids', value_type=list, element_type=int)
    """IDs of ships in the supporting fleet."""

    @property
    def required_objects(self):
        return ['ShipList', 'Preferences']

    def request(self, combined_fleet_deployment, ship_list, preferences):
        combined_fleet_deployment = CombinedFleetDeployment.parse_text(
            combined_fleet_deployment)
        ship_pool = list(ship_list.ships.itervalues())
        # Primary fleet.
        primary_fleet = CombinedFleetDeploymentShipIdList.find_saved_fleet(
            preferences, combined_fleet_deployment.primary_fleet_name)
        self.primary_ship_ids, ship_pool = (
            CombinedFleetDeploymentShipIdList.extract_ids_and_rest(
                primary_fleet.get_ships(ship_pool), ship_pool))
        # Secondary fleet.
        if combined_fleet_deployment.secondary_fleet_name:
            secondary_fleet = (
                CombinedFleetDeploymentShipIdList.find_saved_fleet(
                    preferences,
                    combined_fleet_deployment.secondary_fleet_name))
            self.secondary_ship_ids, ship_pool = (
                CombinedFleetDeploymentShipIdList.extract_ids_and_rest(
                    secondary_fleet.get_ships(ship_pool), ship_pool))
        # Supporting fleet.
        if combined_fleet_deployment.supporting_fleet_name:
            supporting_fleet = (
                CombinedFleetDeploymentShipIdList.find_saved_fleet(
                    preferences,
                    combined_fleet_deployment.supporting_fleet_name))
            self.supporting_ship_ids, ship_pool = (
                CombinedFleetDeploymentShipIdList.extract_ids_and_rest(
                    supporting_fleet.get_ships(ship_pool), ship_pool))
        # Escoting fleet.
        if combined_fleet_deployment.escoting_fleet_name:
            escoting_fleet = (
                CombinedFleetDeploymentShipIdList.find_saved_fleet(
                    preferences,
                    combined_fleet_deployment.escoting_fleet_name))
            self.escoting_ship_ids, ship_pool = (
                CombinedFleetDeploymentShipIdList.extract_ids_and_rest(
                    escoting_fleet.get_ships(ship_pool), ship_pool))
        return self

    @staticmethod
    def find_saved_fleet(preferences, fleet_name):
        matching_fleets = [sf for sf in preferences.fleet_prefs.saved_fleets
                           if sf.name == fleet_name]
        if not matching_fleets:
            raise Exception(u'Saved fleet of name {} was not found.'.format(
                fleet_name))
        return matching_fleets[0]

    @staticmethod
    def extract_ids_and_rest(ships, ship_pool):
        ship_ids = [ship.id for ship in ships]
        rest = [ship for ship in ship_pool if ship not in ships]
        return ship_ids, rest
