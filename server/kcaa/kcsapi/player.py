#!/usr/bin/env python

import datetime
import time

import gviz_api

import jsonobject
import model


class PlayerInfo(model.KCAAObject):
    """Player information."""

    name = jsonobject.JSONProperty('name', value_type=unicode)
    """Name."""
    level = jsonobject.JSONProperty('level', value_type=int)
    """Admiral level."""
    experience = jsonobject.JSONProperty('experience', value_type=int)
    """Admiral experience points."""
    admiral_rank = jsonobject.JSONProperty('admiral_rank', value_type=int)
    """Admiral rank."""
    comment = jsonobject.JSONProperty('comment', value_type=unicode)
    """Player comment."""
    num_fleets = jsonobject.JSONProperty('num_fleets', value_type=int)
    """Number of fleets."""
    num_repair_slots = jsonobject.JSONProperty('num_repair_slots',
                                               value_type=int)
    """Number of repair slots."""
    num_shipyard_slots = jsonobject.JSONProperty('num_shipyard_slots',
                                                 value_type=int)
    """Number of shipyard slots."""
    max_ships = jsonobject.JSONProperty('max_ships', value_type=int)
    """Maximum number of ships."""
    max_equipments = jsonobject.JSONProperty('max_equipments', value_type=int)
    """Maximum number of equipments."""
    max_resouces = jsonobject.JSONProperty('max_resouces', value_type=int)
    """Maximum amount of resources to which they generates over time."""
    num_expedition_wins = jsonobject.JSONProperty('num_expedition_wins',
                                                  value_type=int)
    """Number of expedition wins."""
    num_expedition_losses = jsonobject.JSONProperty('num_expedition_losses',
                                                    value_type=int)
    """Number of expedition losses."""
    num_practice_wins = jsonobject.JSONProperty('num_practice_wins',
                                                value_type=int)
    """Number of practice wins."""
    num_practice_losses = jsonobject.JSONProperty('num_practice_losses',
                                                  value_type=int)
    """Number of practice losses."""
    num_missions = jsonobject.JSONProperty('num_missions', value_type=int)
    """Number of mission trials."""
    num_mission_successes = jsonobject.JSONProperty('num_mission_successes',
                                                    value_type=int)
    """Number of mission successes."""
    furniture_coins = jsonobject.JSONProperty('furniture_coins',
                                              value_type=int)
    """Furniture coins."""

    def update(self, api_name, request, response, objects, debug):
        super(PlayerInfo, self).update(api_name, request, response, objects,
                                       debug)
        if api_name == '/api_get_member/basic':
            self.update_data(response.api_data)
        elif api_name == '/api_port/port':
            self.update_data(response.api_data.api_basic)

    def update_data(self, data):
            self.name = data.api_nickname
            self.level = data.api_level
            self.experience = data.api_experience
            self.admiral_rank = data.api_rank
            self.comment = data.api_comment
            self.num_fleets = data.api_count_deck
            self.num_repair_slots = data.api_count_ndock
            self.num_shipyard_slots = data.api_count_kdock
            self.max_ships = data.api_max_chara
            self.max_equipments = data.api_max_slotitem + 3
            self.max_resources = 1000 + 250 * data.api_level
            self.num_expedition_wins = data.api_st_win
            self.num_expedition_losses = data.api_st_lose
            self.num_practice_wins = data.api_pt_win
            self.num_practice_losses = data.api_pt_lose
            self.num_missions = data.api_ms_count
            self.num_mission_successes = data.api_ms_success
            self.furniture_coins = data.api_fcoin


class PlayerResources(model.KCAAObject):
    """Resources available for the player."""

    fuel = jsonobject.JSONProperty('fuel', value_type=int)
    """Fuel."""
    ammo = jsonobject.JSONProperty('ammo', value_type=int)
    """Ammo."""
    steel = jsonobject.JSONProperty('steel', value_type=int)
    """Steel."""
    bauxite = jsonobject.JSONProperty('bauxite', value_type=int)
    """Bauxite."""
    build_booster = jsonobject.JSONProperty('build_booster', value_type=int)
    """Build booster."""
    repair_booster = jsonobject.JSONProperty('repair_booster', value_type=int)
    """Repair booster."""
    build_material = jsonobject.JSONProperty('build_material', value_type=int)
    """Build material."""

    def update(self, api_name, request, response, objects, debug):
        super(PlayerResources, self).update(api_name, request, response,
                                            objects, debug)
        id_to_field = [
            'fuel',
            'ammo',
            'steel',
            'bauxite',
            'build_booster',
            'repair_booster',
            'build_material',
        ]
        if api_name == '/api_port/port':
            for data in response.api_data.api_material:
                if data.api_id < 1 or data.api_id > len(id_to_field):
                    continue
                setattr(self, id_to_field[data.api_id - 1], data.api_value)
        elif api_name == '/api_req_kousyou/destroyship':
            self.fuel, self.ammo, self.steel, self.bauxite = (
                response.api_data.api_material)


class PlayerResourcesTimeseriesEntry(jsonobject.JSONSerializableObject):

    time = jsonobject.JSONProperty('time', value_type=long)
    """Time of this entry."""
    resources = jsonobject.JSONProperty(
        'resources', value_type=PlayerResources)
    """Player resources of this entry."""


class PlayerResourcesJournal(model.KCAAJournalObject):
    """Journal for player resources."""

    entries = jsonobject.JSONProperty(
        'entries', [], value_type=list,
        element_type=PlayerResourcesTimeseriesEntry)
    """Time series of PlayerResources."""

    @property
    def monitored_objects(self):
        return ['PlayerResources']

    def update(self, api_names, player_resources):
        self.entries.append(PlayerResourcesTimeseriesEntry(
            time=long(time.time()),
            resources=player_resources.clean_copy()))

    def request(self, subtype):
        if subtype == 'basic':
            description = {'datetime': ('datetime', 'Datetime'),
                           'fuel': ('number', 'Fuel'),
                           'ammo': ('number', 'Ammo'),
                           'steel': ('number', 'Steel'),
                           'bauxite': ('number', 'Bauxite')}
            data = [{'datetime': datetime.datetime.fromtimestamp(entry.time),
                     'fuel': entry.resources.fuel,
                     'ammo': entry.resources.ammo,
                     'steel': entry.resources.steel,
                     'bauxite': entry.resources.bauxite}
                    for entry in self.entries]
            data_table = gviz_api.DataTable(description)
            data_table.LoadData(data)
            return data_table.ToJSon(columns_order=[
                'datetime', 'fuel', 'ammo', 'steel', 'bauxite'])
        elif subtype == 'rare':
            description = {'datetime': ('datetime', 'Datetime'),
                           'build_booster': ('number', 'Build booster'),
                           'repair_booster': ('number', 'Repair booster'),
                           'build_material': ('number', 'Build material')}
            data = [{'datetime': datetime.datetime.fromtimestamp(entry.time),
                     'build_booster': entry.resources.build_booster,
                     'repair_booster': entry.resources.repair_booster,
                     'build_material': entry.resources.build_material}
                    for entry in self.entries]
            data_table = gviz_api.DataTable(description)
            data_table.LoadData(data)
            return data_table.ToJSon(columns_order=[
                'datetime', 'build_booster', 'repair_booster',
                'build_material'])
        else:
            return None
