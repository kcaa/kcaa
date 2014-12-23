#!/usr/bin/env python

import logging

import jsonobject
import model


logger = logging.getLogger('kcaa.kcsapi.equipment')


class EquipmentTypeDefinition(jsonobject.JSONSerializableObject):

    id = jsonobject.ReadonlyJSONProperty('id', value_type=int)
    """Slot item type ID."""
    name = jsonobject.ReadonlyJSONProperty('name', value_type=unicode)
    """Slot item type name."""


class EquipmentDefinition(jsonobject.JSONSerializableObject):

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


class EquipmentDefinitionList(model.KCAAObject):
    """List of slot item definitions."""

    types = jsonobject.JSONProperty('types', [], value_type=list,
                                    element_type=EquipmentTypeDefinition)
    """Slot item types."""
    items = jsonobject.JSONProperty('items', {}, value_type=dict,
                                    element_type=EquipmentDefinition)
    """Slot items."""

    def update(self, api_name, request, response, objects, debug):
        super(EquipmentDefinitionList, self).update(
            api_name, request, response, objects, debug)
        for data in response.api_data.api_mst_slotitem_equiptype:
            self.types.append(EquipmentDefinition(
                id=data.api_id,
                name=data.api_name))
        for data in response.api_data.api_mst_slotitem:
            # ID 500 and later are reserved for enemies.
            if data.api_id >= 500:
                continue
            self.items[str(data.api_id)] = EquipmentDefinition(
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


class Equipment(jsonobject.JSONSerializableObject):

    id = jsonobject.ReadonlyJSONProperty('id', value_type=int)
    """Instance ID."""
    item_id = jsonobject.ReadonlyJSONProperty('item_id', value_type=int)
    """Item definition ID."""
    level = jsonobject.ReadonlyJSONProperty('level', value_type=int)
    """Enhancement level."""
    locked = jsonobject.ReadonlyJSONProperty('locked', value_type=bool)
    """True if this item is locked."""

    def definition(self, equipment_definition_list):
        return equipment_definition_list.items[str(self.item_id)]

    @staticmethod
    def compare(equipment_a, equipment_b):
        # This might be suboptimal. Use the sort order of the definition.
        if equipment_a.item_id != equipment_b.item_id:
            return equipment_a.item_id - equipment_b.item_id
        # Items are reversed in terms of instance IDs; newer items come first.
        return -(equipment_a.id - equipment_b.id)


class EquipmentIdList(jsonobject.JSONSerializableObject):

    item_ids = jsonobject.JSONProperty('item_ids', value_type=list,
                                       element_type=int)


class EquipmentList(model.KCAAObject):

    items = jsonobject.JSONProperty('items', {}, value_type=dict,
                                    element_type=Equipment)
    """Slot items."""
    item_instances = jsonobject.JSONProperty(
        'item_instances', {}, value_type=dict, element_type=EquipmentIdList)
    """Instances of each slot item definition.

    Keyed by the slot item definition ID, this map contains the list of slot
    item instances.
    """

    def get_unequipped_items(self, ship_list):
        equipped_item_ids = set()
        for ship in ship_list.ships.itervalues():
            for equipment_id in ship.equipment_ids:
                if equipment_id != -1:
                    equipped_item_ids.add(equipment_id)
        items = [item for item in self.items.values() if
                 item.id not in equipped_item_ids]
        items.sort(Equipment.compare)
        return items

    def compute_page_position(self, equipment_id, unequipped_items):
        for index, item in enumerate(unequipped_items):
            if item.id != equipment_id:
                continue
            page = 1 + index / 10
            in_page_index = index % 10
            return page, in_page_index
        return None, None

    def get_max_page(self, items):
        return (len(items) + 9) / 10

    def update(self, api_name, request, response, objects, debug):
        super(EquipmentList, self).update(api_name, request, response, objects,
                                          debug)
        if api_name == '/api_get_member/slot_item':
            self.items.clear()
            self.item_instances.clear()
            for data in response.api_data:
                self.add_item(Equipment(
                    id=data.api_id,
                    item_id=data.api_slotitem_id,
                    level=data.api_level,
                    locked=data.api_locked != 0))
        elif api_name == '/api_req_kousyou/createitem':
            if response.api_data.api_create_flag:
                data = response.api_data.api_slot_item
                self.add_item(Equipment(
                    id=data.api_id,
                    item_id=data.api_slotitem_id,
                    level=0,
                    locked=False))
        elif api_name == '/api_req_kousyou/destroyitem2':
            for instance_id in request.api_slotitem_ids.split(','):
                self.remove_item(instance_id)
        elif api_name == '/api_req_kousyou/destroyship':
            ship_list = objects.get('ShipList')
            if not ship_list:
                logger.error('ShipList not found when destroying a ship.')
                return
            ship = ship_list.ships[request.api_ship_id]
            for equipment_id in ship.equipment_ids:
                if equipment_id != -1:
                    self.remove_item(equipment_id)

        elif api_name == '/api_req_kousyou/getship':
            for data in response.api_data.api_slotitem:
                self.add_item(Equipment(
                    id=data.api_id,
                    item_id=data.api_slotitem_id,
                    level=0,
                    locked=False))

    def add_item(self, item):
        self.items[str(item.id)] = item
        item_id = str(item.item_id)
        if item_id in self.item_instances:
            self.item_instances[item_id].item_ids.append(item.id)
        else:
            self.item_instances[item_id] = EquipmentIdList(item_ids=[item.id])

    def remove_item(self, instance_id):
        item = self.items[str(instance_id)]
        del self.items[str(instance_id)]
        self.item_instances[str(item.item_id)].item_ids.remove(item.id)
