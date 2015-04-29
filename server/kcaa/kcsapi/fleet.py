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

    @property
    def ready(self):
        return not self.mission_id


class FleetList(model.KCAAObject):
    """List of fleets (decks)."""

    fleets = jsonobject.JSONProperty('fleets', [], value_type=list,
                                     element_type=Fleet)
    """Fleets.

    Note that this list has 0-origin, while other objects use 1-origin index to
    reference a fleet."""
    combined = jsonobject.JSONProperty('combined', value_type=bool)
    """Whether the fleets are combined."""
    combined_fleet_type = jsonobject.JSONProperty('combined_fleet_type',
                                                  value_type=int)
    """Type of the combined fleet."""
    COMBINED_FLEET_TYPE_SINGLE = 0
    # Single fleet.
    COMBINED_FLEET_TYPE_MOBILE = 1
    # Mobile fleet, with plenty of aircraft carriers.
    COMBINED_FLEET_TYPE_SURFACE = 2
    # Surface ship fleet, a usual fleet with battleships or cruisers.

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
            if hasattr(response.api_data, 'api_combined_flag'):
                combined_flag = response.api_data.api_combined_flag
                self.combined = combined_flag != 0
                self.combined_fleet_type = combined_flag
            else:
                self.combined = False
                self.combined_fleet_type = FleetList.COMBINED_FLEET_TYPE_SINGLE
        elif api_name == '/api_get_member/deck':
            self.update_fleets(response.api_data, ship_list)
        elif api_name == '/api_get_member/ship3':
            self.update_fleets(response.api_data.api_deck_data, ship_list)
        elif api_name == '/api_req_hensei/combined':
            combined_flag = int(request.api_combined_type)
            self.combined = combined_flag != 0
            self.combined_fleet_type = combined_flag
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

    def get_ships(self, ship_pool, equipment_pool, ship_def_list,
                  equipment_list, equipment_def_list, equipment_prefs):
        # TODO: Unit test.
        ship_pool = list(ship_pool)[:]
        equipment_pool = list(equipment_pool)[:]
        if self.global_predicate:
            ship_pool = [s for s in ship_pool if
                         self.global_predicate.apply(s)]
        entries = []
        for ship_requirement in self.ship_requirements:
            predicate = ship_requirement.predicate
            applicable_ships = [s for s in ship_pool if predicate.apply(s)]
            ship_requirement.sorter.sort(applicable_ships)
            applicable_ship = None
            applicable_equipments = None
            if not applicable_ships:
                pass
            elif not ship_requirement.equipment_deployment:
                applicable_ship = applicable_ships[0]
            else:
                equipment_deployment = equipment_prefs.get_deployment(
                    ship_requirement.equipment_deployment)
                equipment_pool_ids = frozenset([e.id for e in equipment_pool])
                for target_ship in applicable_ships:
                    current_equipments = [
                        equipment_list.items[str(e_id)] for e_id in
                        target_ship.equipment_ids if
                        e_id > 0 and e_id in equipment_pool_ids]
                    other_equipments = [
                        equipment for equipment in equipment_pool if
                        equipment not in current_equipments]
                    # Prefer currently equipped items.
                    # This avoids unnecessary equipment swap when equipments
                    # are loaded from the top to bottom.
                    # TODO: Handle the case with most aircraft capacity.
                    possible, equipments = equipment_deployment.get_equipments(
                        target_ship, current_equipments + other_equipments,
                        ship_def_list, equipment_def_list)
                    if possible:
                        applicable_ship = target_ship
                        applicable_equipments = equipments
                        equipment_pool = [e for e in equipment_pool if
                                          e not in equipments]
                        break
            if not applicable_ship:
                if not ship_requirement.omittable:
                    entries.append([ship.Ship(id=-1), None])
                else:
                    entries.append([ship.Ship(id=0), None])
            else:
                entries.append([applicable_ship, applicable_equipments])
                ship_pool.remove(applicable_ship)
        return entries

    def are_all_ships_ready(self, ship_list, ship_def_list, equipment_list,
                            equipment_def_list, eqiupment_prefs,
                            recently_used_equipments):
        return all([s[0].id == 0 or s[0].ready for s in
                    self.get_ships(
                        ship_list.ships.values(),
                        equipment_list.get_available_equipments(
                            recently_used_equipments, ship_list),
                        ship_def_list,
                        equipment_list,
                        equipment_def_list,
                        eqiupment_prefs)])


class FleetDeploymentShipIdList(ship.ShipIdList):

    @property
    def required_objects(self):
        return ['ShipDefinitionList', 'ShipList', 'EquipmentDefinitionList',
                'EquipmentList', 'Preferences']

    @property
    def required_states(self):
        return ['RecentlyUsedEquipments']

    def request(self, fleet_deployment, ship_definition_list, ship_list,
                equipment_definition_list, equipment_list, preferences,
                recently_used_equipments):
        fleet_deployment = FleetDeployment.parse_text(fleet_deployment)
        ship_pool = ship_list.ships.values()
        equipment_pool = equipment_list.get_available_equipments(
            recently_used_equipments, ship_list)
        entries = fleet_deployment.get_ships(
            ship_pool, equipment_pool, ship_definition_list, equipment_list,
            equipment_definition_list, preferences.equipment_prefs)
        self.ship_ids = [e[0].id for e in entries]
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
    escoting_fleet_name = jsonobject.JSONProperty('escoting_fleet_name',
                                                  value_type=unicode)
    """Name of the fleet escoting the primary fleet the whole way before the
    boss fleet. Can be null if no fleet is needed."""
    supporting_fleet_name = jsonobject.JSONProperty('supporting_fleet_name',
                                                    value_type=unicode)
    """Name of the fleet supporting the primary fleet in the battle against the
    boss fleet. Can be null if no fleet is needed."""

    def get_ships(self, ship_list, fleet_list, ship_def_list, equipment_list,
                  equipment_def_list, preferences, recently_used_equipments):
        # TODO: Refactor this method. Too long!!! Too many boilerplates!
        # NOTE: Unlike FleetDeployment.get_ships(), this method doesn't return
        # the entries of ship ID and equipment list pairs.
        id_list = CombinedFleetDeploymentShipIdList()
        ship_pool = ship_list.ships.values()
        equipment_pool = equipment_list.get_available_equipments(
            recently_used_equipments, ship_list)
        id_list.available_fleet_ids = [fleet.id for fleet in fleet_list.fleets
                                       if fleet.ready]
        # Primary fleet.
        primary_fleet = CombinedFleetDeployment.find_saved_fleet(
            preferences, self.primary_fleet_name)
        id_list.primary_ship_ids, ship_pool, equipment_pool = (
            CombinedFleetDeployment.extract_ids_and_rest(
                primary_fleet.get_ships(
                    ship_pool, equipment_pool, ship_def_list, equipment_list,
                    equipment_def_list, preferences.equipment_prefs),
                ship_pool, equipment_pool))
        id_list.loadable = CombinedFleetDeployment.fleet_loadable(
            id_list.primary_ship_ids)
        num_fleets = 1
        # Secondary fleet.
        if self.secondary_fleet_name:
            secondary_fleet = CombinedFleetDeployment.find_saved_fleet(
                preferences, self.secondary_fleet_name)
            id_list.secondary_ship_ids, ship_pool, equipment_pool = (
                CombinedFleetDeployment.extract_ids_and_rest(
                    secondary_fleet.get_ships(
                        ship_pool, equipment_pool, ship_def_list,
                        equipment_list, equipment_def_list,
                        preferences.equipment_prefs),
                    ship_pool, equipment_pool))
            id_list.loadable = (
                id_list.loadable and
                2 in id_list.available_fleet_ids and
                CombinedFleetDeployment.fleet_loadable(
                    id_list.secondary_ship_ids))
            num_fleets += 1
        # Supporting fleet.
        if self.supporting_fleet_name:
            supporting_fleet = CombinedFleetDeployment.find_saved_fleet(
                preferences, self.supporting_fleet_name)
            id_list.supporting_ship_ids, ship_pool, equipment_pool = (
                CombinedFleetDeployment.extract_ids_and_rest(
                    supporting_fleet.get_ships(
                        ship_pool, equipment_pool, ship_def_list,
                        equipment_list, equipment_def_list,
                        preferences.equipment_prefs),
                    ship_pool, equipment_pool))
            id_list.loadable = (
                id_list.loadable and
                CombinedFleetDeployment.fleet_loadable(
                    id_list.supporting_ship_ids))
            num_fleets += 1
        # Escoting fleet.
        if self.escoting_fleet_name:
            escoting_fleet = CombinedFleetDeployment.find_saved_fleet(
                preferences, self.escoting_fleet_name)
            id_list.escoting_ship_ids, ship_pool, equipment_pool = (
                CombinedFleetDeployment.extract_ids_and_rest(
                    escoting_fleet.get_ships(
                        ship_pool, equipment_pool, ship_def_list,
                        equipment_list, equipment_def_list,
                        preferences.equipment_prefs),
                    ship_pool, equipment_pool))
            id_list.loadable = (
                id_list.loadable and
                CombinedFleetDeployment.fleet_loadable(
                    id_list.escoting_ship_ids))
            num_fleets += 1
        id_list.loadable = (id_list.loadable and
                            len(id_list.available_fleet_ids) >= num_fleets)
        return id_list

    @staticmethod
    def find_saved_fleet(preferences, fleet_name):
        matching_fleets = [sf for sf in preferences.fleet_prefs.saved_fleets
                           if sf.name == fleet_name]
        if not matching_fleets:
            raise Exception(u'Saved fleet of name {} was not found.'.format(
                fleet_name))
        return matching_fleets[0]

    @staticmethod
    def extract_ids_and_rest(entries, ship_pool, equipment_pool):
        ship_ids = [e[0].id for e in entries]
        ships = frozenset([e[0] for e in entries])
        ship_pool_rest = [s for s in ship_pool if s not in ships]
        equipment_ids = set()
        for entry in entries:
            if entry[1]:
                equipment_ids.union([e.id for e in entry[1]])
        equipment_pool_rest = [e for e in equipment_pool if
                               e.id not in equipment_ids]
        return ship_ids, ship_pool_rest, equipment_pool_rest

    @staticmethod
    def fleet_loadable(ship_ids):
        return all([ship_id != -1 for ship_id in ship_ids])


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
    available_fleet_ids = jsonobject.JSONProperty(
        'available_fleet_ids', value_type=list, element_type=int)
    """IDs of available fleets."""
    loadable = jsonobject.JSONProperty('loadable', value_type=bool)
    """Whether this combined fleet can be loadable immediately."""

    @property
    def required_objects(self):
        return ['ShipDefinitionList', 'ShipList', 'FleetList',
                'EquipmentDefinitionList', 'EquipmentList', 'Preferences']

    @property
    def required_states(self):
        return ['RecentlyUsedEquipments']

    def request(self, combined_fleet_deployment, ship_definition_list,
                ship_list, fleet_list, equipment_definition_list,
                equipment_list, preferences, recently_used_equipments):
        combined_fleet_deployment = CombinedFleetDeployment.parse_text(
            combined_fleet_deployment)
        return combined_fleet_deployment.get_ships(
            ship_list, fleet_list, ship_definition_list, equipment_list,
            equipment_definition_list, preferences, recently_used_equipments)
