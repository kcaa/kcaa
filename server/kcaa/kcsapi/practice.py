#!/usr/bin/env python

import jsonobject
import model


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

    id = jsonobject.ReadonlyJSONProperty('id', value_type=int)
    """ID."""
    member_id = jsonobject.ReadonlyJSONProperty('member_id', value_type=int)
    """ID of the member (player)."""
    enemy_name = jsonobject.ReadonlyJSONProperty('enemy_name',
                                                 value_type=unicode)
    """Enemy name."""
    enemy_comment = jsonobject.ReadonlyJSONProperty('enemy_comment',
                                                    value_type=unicode)
    """Enemy comment."""
    enemy_level = jsonobject.ReadonlyJSONProperty('enemy_level',
                                                  value_type=int)
    """Enemy level."""
    enemy_rank = jsonobject.ReadonlyJSONProperty('enemy_rank',
                                                 value_type=unicode)
    """Enemy rank."""
    result = jsonobject.JSONProperty('result', value_type=int)
    """Resuslt of the practice."""
    STATE_NEW = 0
    STATE_E = 1
    STATE_D = 2
    STATE_C = 3
    STATE_B = 4
    STATE_A = 5
    STATE_S = 6
    fleet_name = jsonobject.JSONProperty('fleet_name', value_type=unicode)
    """Fleet name."""
    ships = jsonobject.JSONProperty('ships', value_type=list,
                                    element_type=ShipEntry)
    """Ships belonging to this practice fleet."""


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
                practice = Practice(
                    id=data.api_id,
                    member_id=data.api_enemy_id,
                    enemy_name=data.api_enemy_name,
                    enemy_comment=data.api_enemy_comment,
                    enemy_level=data.api_enemy_level,
                    enemy_rank=data.api_enemy_rank,
                    result=data.api_state)
                if len(old_practices) > i:
                    practice.ships = old_practices[i].ships
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
