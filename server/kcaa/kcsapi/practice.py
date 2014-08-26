#!/usr/bin/env python

import jsonobject
import model
import ship


class ShipEntry(jsonobject.JSONSerializableObject):

    ship_id = jsonobject.ReadonlyJSONProperty('ship_id', value_type=int)
    """Ship definition ID."""
    level = jsonobject.ReadonlyJSONProperty('level', value_type=int)
    """Level."""
    name = jsonobject.ReadonlyJSONProperty('name', value_type=unicode)
    """Name."""
    ship_type = jsonobject.ReadonlyJSONProperty('ship_type', value_type=int)
    """Ship type."""


class Practice(jsonobject.JSONSerializableObject):

    id = jsonobject.JSONProperty('id', value_type=int)
    """ID."""
    member_id = jsonobject.JSONProperty('member_id', value_type=int)
    """ID of the member (player)."""
    enemy_name = jsonobject.JSONProperty('enemy_name', value_type=unicode)
    """Enemy name."""
    enemy_comment = jsonobject.JSONProperty('enemy_comment',
                                            value_type=unicode)
    """Enemy comment."""
    enemy_level = jsonobject.JSONProperty('enemy_level', value_type=int)
    """Enemy level."""
    enemy_rank = jsonobject.JSONProperty('enemy_rank', value_type=unicode)
    """Enemy rank."""
    result = jsonobject.JSONProperty('result', value_type=int)
    """Resuslt of the practice."""
    RESULT_NEW = 0
    RESULT_E = 1
    RESULT_D = 2
    RESULT_C = 3
    RESULT_B = 4
    RESULT_A = 5
    RESULT_S = 6
    fleet_name = jsonobject.JSONProperty('fleet_name', value_type=unicode)
    """Fleet name."""
    ships = jsonobject.JSONProperty('ships', value_type=list,
                                    element_type=ShipEntry)
    """Ships belonging to this practice fleet."""
    fleet_type = jsonobject.JSONProperty('fleet_type', value_type=int)
    """Type of the fleet.

    This is a simple categorization of the opponent fleet. This is designed to
    be much simpler compared to a tag-based approach, which may supersede this
    categorization in the future."""
    FLEET_TYPE_GENERIC = 0
    FLEET_TYPE_SUBMARINES = 1
    FLEET_TYPE_NO_ANTI_SUBMARINE = 2
    FLEET_TYPE_AIRCRAFT_CARRIERS = 3
    FLEET_TYPE_BATTLESHIPS = 4
    FLEET_TYPE_HEAVY_CRUISERS = 5
    FLEET_TYPE_LIGHT_CRUISERS = 6
    FLEET_TYPE_DESTROYERS = 7

    @staticmethod
    def get_fleet_type(ships):
        # Inverse N (number of ships)
        inv_n = 1.0 / len(ships)
        num_submarines = len(filter(
            ship.ShipDefinition.is_submarine, ships))
        is_submarine_flagship = ship.ShipDefinition.is_submarine(ships[0])
        # "Submarines" if more than half of them are submarines or the flag
        # ship is a submarine.
        if inv_n * num_submarines >= 0.55 or is_submarine_flagship:
            return Practice.FLEET_TYPE_SUBMARINES
        num_anti_submarines = len(filter(
            ship.ShipDefinition.is_anti_submarine, ships))
        # "No anti submarine" if no anti submarine ship.
        if num_anti_submarines == 0:
            return Practice.FLEET_TYPE_NO_ANTI_SUBMARINE
        num_aircraft_carriers = len(filter(
            ship.ShipDefinition.is_aircraft_carrier, ships))
        # "Aircraft carriers" if half of them are aircraft carriers.
        if inv_n * num_aircraft_carriers >= 0.5:
            return Practice.FLEET_TYPE_AIRCRAFT_CARRIERS
        num_battleships = len(filter(ship.ShipDefinition.is_battleship, ships))
        # "Battleships" if half of them are battleships or aircraft carriers.
        if inv_n * (num_battleships + num_aircraft_carriers) >= 0.5:
            return Practice.FLEET_TYPE_BATTLESHIPS
        num_heavy_cruisers = len(filter(
            ship.ShipDefinition.is_heavy_cruiser, ships))
        # "Heavy cruisers" if half of them are heavy cruisers or aircraft
        # carriers.
        if inv_n * (num_heavy_cruisers + num_aircraft_carriers) >= 0.5:
            return Practice.FLEET_TYPE_HEAVY_CRUISERS
        num_light_cruisers = len(filter(
            ship.ShipDefinition.is_light_cruiser, ships))
        # "Light cruisers" if more than half of them are light cruisers.
        if inv_n * num_light_cruisers >= 0.55:
            return Practice.FLEET_TYPE_LIGHT_CRUISERS
        num_destroyers = len(filter(
            lambda s: s.ship_type == ship.ShipDefinition.SHIP_TYPE_DESTROYER,
            ships))
        # "Destroyers" if more than half of them are destroyers.
        if inv_n * num_destroyers >= 0.55:
            return Practice.FLEET_TYPE_DESTROYERS
        # "Generic" if no significant ship type is outstanding.
        return Practice.FLEET_TYPE_GENERIC


class PracticeList(model.KCAAObject):

    practices = jsonobject.JSONProperty('practices', [], value_type=list,
                                        element_type=Practice)
    """Practice instances."""

    def find_practice_by_member_id(self, member_id):
        practices = filter(lambda p: p.member_id == member_id, self.practices)
        return practices[0] if practices else None

    def update(self, api_name, request, response, objects, debug):
        super(PracticeList, self).update(api_name, request, response, objects,
                                         debug)
        if api_name == '/api_get_member/practice':
            old_practices = self.practices
            self.practices = []
            for i, data in enumerate(response.api_data):
                if len(old_practices) > i:
                    practice = old_practices[i]
                else:
                    practice = Practice()
                practice.id = data.api_id
                practice.member_id = data.api_enemy_id
                practice.enemy_name = data.api_enemy_name
                practice.enemy_comment = data.api_enemy_comment
                practice.enemy_level = data.api_enemy_level
                practice.enemy_rank = data.api_enemy_rank
                practice.result = data.api_state
                self.practices.append(practice)
        elif api_name == '/api_req_member/get_practice_enemyinfo':
            ship_defs = objects['ShipDefinitionList'].ships
            practice = self.find_practice_by_member_id(
                response.api_data.api_member_id)
            if not practice:
                return
            practice.fleet_name = response.api_data.api_deckname
            practice.ships = []
            for data in response.api_data.api_deck.api_ships:
                if data.api_id == -1:
                    continue
                ship_def = ship_defs[str(data.api_ship_id)]
                practice.ships.append(ShipEntry(
                    ship_id=ship_def.id,
                    level=data.api_level,
                    name=ship_def.name,
                    ship_type=ship_def.ship_type))
            practice.fleet_type = Practice.get_fleet_type(practice.ships)
