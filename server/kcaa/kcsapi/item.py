#!/usr/bin/env python

import logging

import jsonobject
import model


logger = logging.getLogger('kcaa.kcsapi.item')


class SlotItemTypeDefinition(jsonobject.JSONSerializableObject):

    id = jsonobject.ReadonlyJSONProperty('id', value_type=int)
    """Slot item type ID."""
    name = jsonobject.ReadonlyJSONProperty('name', value_type=unicode)
    """Slot item type name."""


class SlotItemDefinition(jsonobject.JSONSerializableObject):

    id = jsonobject.ReadonlyJSONProperty('id', value_type=int)
    """Slot item definition ID."""
    name = jsonobject.ReadonlyJSONProperty('name', value_type=unicode)
    """Slot item name."""
    type = jsonobject.ReadonlyJSONProperty('type', value_type=int)
    """Slot item type."""
    TYPE_SMALL_CALIBER_PRIMARY_CANNON = 1
    TYPE_MEDIUM_CALIBER_PRIMARY_CANNON = 2
    TYPE_LARGE_CALIBER_PRIMARY_CANNON = 3
    TYPE_SECONDARY_CANNON = 4
    TYPE_TORPEDO = 5
    TYPE_FIGTHER_AIRCRAFT = 6
    TYPE_DIVE_BOMBER_AIRCRAFT = 7
    TYPE_TORPEDO_BOMBER_AIRCRAFT = 8
    TYPE_RECONNAISSANCE_AIRCRAFT = 9
    TYPE_RECONNAISSANCE_SEAPLANE = 10
    TYPE_DIVE_BOMBER_SEAPLANE = 11
    TYPE_SMALL_RADER = 12
    TYPE_LARGE_RADER = 13
    TYPE_SONAR = 14
    TYPE_DEPTH_CHARGE = 15
    TYPE_ADDITIONAL_ARMOR = 16
    TYPE_ENGINE_ENHANCER = 17
    TYPE_ANTI_AIR_AMMO = 18
    TYPE_ANTI_SHIP_AMMO = 19
    TYPE_VARIABLE_TIME_FUZE = 20
    TYPE_ANTI_AIR_MACHINE_GUN = 21
    TYPE_MIDGET_SUBMARINE = 22
    TYPE_FIRST_AID_PERSONNEL = 23
    TYPE_LANDING_CRAFT = 24
    TYPE_AUTOGYRO = 25
    TYPE_MARITIME_PATROL_AIRCRAFT = 26
    TYPE_MEDIUM_ADDITIONAL_ARMOR = 27
    TYPE_LARGE_ADDITIONAL_ARMOR = 28
    TYPE_SEARCHLIGHT = 29
    TYPE_SUPPLY_CARRIER = 30
    TYPE_SHIP_REPAIRER = 31
    TYPE_SUBMARINE_TORPEDO = 32
    TYPE_FLARE = 33
    TYPE_HEADQUARTER = 34
    TYPE_AIRFORCE_PERSONNEL = 35
    TYPE_ANTI_AIR_FIRE_CONTROL_SYSTEM = 36
    type_name = jsonobject.ReadonlyJSONProperty(
        'type_name', value_type=unicode)
    """Slot item type name."""
    description = jsonobject.ReadonlyJSONProperty(
        'description', value_type=unicode)
    armor = jsonobject.ReadonlyJSONProperty('armor', value_type=int)
    """Armor extension."""
    firepower = jsonobject.ReadonlyJSONProperty('firepower', value_type=int)
    """Firepower extension."""
    fire_hit = jsonobject.ReadonlyJSONProperty('fire_hit', value_type=int)
    """Fire hit probability extension."""
    fire_flee = jsonobject.ReadonlyJSONProperty('fire_flee', value_type=int)
    """Fire flee probability extension."""
    thunderstroke = jsonobject.ReadonlyJSONProperty(
        'thunderstroke', value_type=int)
    """Thunderstroke extension."""
    torpedo_hit = jsonobject.ReadonlyJSONProperty(
        'torpedo_hit', value_type=int)
    """Torpedo hit probability extension."""
    anti_air = jsonobject.ReadonlyJSONProperty('anti_air', value_type=int)
    """Anti air extension."""
    anti_submarine = jsonobject.ReadonlyJSONProperty(
        'anti_submarine', value_type=int)
    """Anti submarine extension."""
    bomb_power = jsonobject.ReadonlyJSONProperty('bomb_power', value_type=int)
    """Dive bomber power extension."""
    scouting = jsonobject.ReadonlyJSONProperty('scouting', value_type=int)
    """Scouting extension."""
    firing_range = jsonobject.ReadonlyJSONProperty('firing_range',
                                                   value_type=int)
    """Firing range."""
    FIRING_RANGE_SHORT = 1
    FIRING_RANGE_MIDDLE = 2
    FIRING_RANGE_LONG = 3
    FIRING_RANGE_VERY_LONG = 4
    rarity = jsonobject.ReadonlyJSONProperty('rarity', value_type=int)
    """Rarity."""
    RARITY_COMMON = 0
    RARITY_RARE = 1
    RARITY_SUPER_RARE = 2
    sort_order = jsonobject.ReadonlyJSONProperty('sort_order', value_type=int)
    """Sort order, or the encyclopedia ID."""


class SlotItemDefinitionList(model.KCAAObject):
    """List of slot item definitions."""

    types = jsonobject.JSONProperty('types', [], value_type=list,
                                    element_type=SlotItemTypeDefinition)
    """Slot item types."""
    items = jsonobject.JSONProperty('items', {}, value_type=dict,
                                    element_type=SlotItemDefinition)
    """Slot items."""

    def update(self, api_name, request, response, objects, debug):
        super(SlotItemDefinitionList, self).update(api_name, request, response,
                                                   objects, debug)
        for data in response.api_data.api_mst_slotitem_equiptype:
            self.types.append(SlotItemDefinition(
                id=data.api_id,
                name=data.api_name))
        for data in response.api_data.api_mst_slotitem:
            self.items[str(data.api_id)] = SlotItemDefinition(
                id=data.api_id,
                name=data.api_name,
                type=data.api_type[2],
                type_name=self.types[data.api_type[2] - 1].name,
                description=data.api_info,
                armor=data.api_souk,
                firepower=data.api_houg,
                fire_hit=data.api_houm,
                fire_flee=data.api_houk,
                thunderstroke=data.api_raig,
                torpedo_hit=data.api_raim,
                anti_air=data.api_tyku,
                anti_submarine=data.api_tais,
                bomb_power=data.api_baku,
                scouting=data.api_saku,
                firing_range=data.api_leng,
                rarity=data.api_rare,
                sort_order=data.api_sortno)
            # Unknown fields
            #   api_broken: required resource amount for repair/charge?
            #   api_type: index 0, 1, 3
            #   api_luck: luck?
            #   api_soku: cruising speed?
            #   api_raik: torpedo flee? (RAIgeki Kaihi)
            #   api_usebull: ? (string) "0"
            #   api_sakb, api_taik, api_atap
