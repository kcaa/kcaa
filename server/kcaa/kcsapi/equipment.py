#!/usr/bin/env python

import logging

import jsonobject
import model
import ship


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
    RARITY_UNCOMMON = 1
    RARITY_RARE = 2
    RARITY_SUPER_RARE = 3
    RARITY_PRECIOUS = 4
    RARITY_DEVINE = 5
    sort_order = jsonobject.ReadonlyJSONProperty('sort_order', value_type=int)
    """Sort order, or the encyclopedia ID."""

    # Some equipment items have a special type. A 51 cm gun (ID 128) is a good
    # example. It's classified as type 3 but it's actually of type 38.
    SPECIAL_ID_TO_TYPE_MAP = {
        128: 38,
    }

    @property
    def powerup_score(self):
        return (2 * self.armor +
                4 * self.firepower +
                5 * self.fire_hit +
                2 * self.fire_flee +
                4 * self.thunderstroke +
                0 * self.torpedo_hit +
                4 * self.anti_air +
                2 * self.anti_submarine +
                3 * self.bomb_power +
                2 * self.scouting +
                1 * self.firing_range +
                6 * self.rarity)


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
            type = data.api_type[2]
            if data.api_id in EquipmentDefinition.SPECIAL_ID_TO_TYPE_MAP:
                type = EquipmentDefinition.SPECIAL_ID_TO_TYPE_MAP[data.api_id]
            self.items[str(data.api_id)] = EquipmentDefinition(
                id=data.api_id,
                name=data.api_name,
                type=type,
                type_name=self.types[type - 1].name,
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
    locked = jsonobject.JSONProperty('locked', value_type=bool)
    """True if this item is locked."""
    # Following properties are just for internal use. Better to hide as normal
    # Python instance members?
    type = jsonobject.ReadonlyJSONProperty('type', value_type=int)
    """Equipment type, derived from the definition."""
    in_type_index = jsonobject.JSONProperty(
        'in_type_index', -1, value_type=int)
    """The position in the equipment list within items that share the type.

    For some unknown reason, the KanColle client seems not to define a
    deterministic natural order for equipment items. Instead, there is a
    dedicated KCSAPI with a mysterious name (/api_get_member/unsetslot -- just
    reused?) to hold the sort order of them per equipment item type.

    This index is 0-origin.
    """
    sort_order = jsonobject.ReadonlyJSONProperty('sort_order', value_type=int)
    """Sort order, or the encyclopedia ID."""
    powerup_score = jsonobject.ReadonlyJSONProperty(
        'powerup_score', 0, value_type=int)
    """Score of the power up that this equipment provides.

    The value is determined by the predefined formula. There is a plan to make
    it possible to customize it.
    """

    def definition(self, equipment_def_list):
        return equipment_def_list.items[str(self.item_id)]

    def __cmp__(self, other):
        if self.type != other.type:
            return self.type - other.type
        return self.in_type_index - other.in_type_index

    @staticmethod
    def compare_on_reassignment(equipment_a, equipment_b):
        """Special compare function used when reassignment happens.

        See :meth:`EquipmentList.reassign_in_type_index` for details."""
        if equipment_a.type != equipment_b.type:
            return equipment_a.type - equipment_b.type
        if equipment_a.sort_order != equipment_b.sort_order:
            return equipment_a.sort_order - equipment_b.sort_order
        return equipment_a.id - equipment_b.id


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

    The order doesn't matter; a client is responsible for sorting actual
    equipment instances if any.
    """

    def get_unequipped_items(self, ship_list):
        equipped_item_ids = set()
        for ship in ship_list.ships.itervalues():
            for equipment_id in ship.equipment_ids:
                if equipment_id != -1:
                    equipped_item_ids.add(equipment_id)
        items = [item for item in self.items.values() if
                 item.id not in equipped_item_ids]
        items.sort()
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
        equipment_def_list = objects['EquipmentDefinitionList']
        if api_name == '/api_get_member/slot_item':
            self.items.clear()
            self.item_instances.clear()
            for data in response.api_data:
                definition = equipment_def_list.items[
                    str(data.api_slotitem_id)]
                self.add_item(Equipment(
                    id=data.api_id,
                    item_id=data.api_slotitem_id,
                    level=data.api_level,
                    locked=data.api_locked != 0,
                    type=definition.type,
                    sort_order=definition.sort_order,
                    powerup_score=definition.powerup_score))
                # in_type_index will soon be overwritten by upcoming unsetslot
                # call.
        elif api_name == '/api_get_member/unsetslot':
            for equipment_type in equipment_def_list.types:
                equipment_ids = getattr(
                    response.api_data,
                    'api_slottype{}'.format(equipment_type.id))
                if equipment_ids == -1:
                    continue
                # Usually unsetslot happens after slot_item, however, when a
                # new item of an unseen type has arrived, unsetslot might
                # precede slot_item. Ignore the key error as another unsetslot
                # would follow slot_item KCSAPI.
                for i, equipment_id in enumerate(equipment_ids):
                    item = self.items.get(str(equipment_id))
                    if item:
                        item.in_type_index = i
        elif api_name == '/api_req_kaisou/lock':
            self.items[request.api_slotitem_id].locked = (
                response.api_data.api_locked == 1)
            # For the record, here is a good place to output eqiupment item ID
            # to check how equipment items are sorted.
            # logger.debug(request.api_slotitem_id)
        elif api_name == '/api_req_kaisou/slotset':
            # This handles both setting and unsetting an equipment.
            # In either case in type indices are reassigned.
            self.reassign_in_type_index(equipment_def_list)
        elif api_name == '/api_req_kaisou/unsetslot_all':
            self.reassign_in_type_index(equipment_def_list)
        elif api_name == '/api_req_kousyou/createitem':
            if response.api_data.api_create_flag:
                data = response.api_data.api_slot_item
                definition = equipment_def_list.items[
                    str(data.api_slotitem_id)]
                self.add_item(Equipment(
                    id=data.api_id,
                    item_id=data.api_slotitem_id,
                    level=0,
                    locked=False,
                    type=definition.type,
                    sort_order=definition.sort_order,
                    powerup_score=definition.powerup_score))
                # Assign in_type_index.
                for i, equipment_id in enumerate(
                        response.api_data.api_unsetslot):
                    self.items[str(equipment_id)].in_type_index = i
        elif api_name == '/api_req_kousyou/destroyitem2':
            for instance_id in request.api_slotitem_ids.split(','):
                self.remove_item(instance_id)
            # No in_type_index is reassigned.
        elif api_name == '/api_req_kousyou/destroyship':
            ship_list = objects.get('ShipList')
            if not ship_list:
                logger.error('ShipList not found when destroying a ship.')
                return
            ship = ship_list.ships[request.api_ship_id]
            for equipment_id in ship.equipment_ids:
                if equipment_id != -1:
                    self.remove_item(equipment_id)
            # No in_type_index is reassigned.
        elif api_name == '/api_req_kousyou/getship':
            if hasattr(response.api_data, 'api_slotitem'):
                for data in response.api_data.api_slotitem:
                    definition = equipment_def_list.items[
                        str(data.api_slotitem_id)]
                    self.add_item(Equipment(
                        id=data.api_id,
                        item_id=data.api_slotitem_id,
                        level=0,
                        locked=False,
                        type=definition.type,
                        sort_order=definition.sort_order,
                        powerup_score=definition.powerup_score))
                # No in_type_index is reassigned.

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

    def reassign_in_type_index(self, equipment_def_list):
        for equipment_type in equipment_def_list.types:
            items_for_type = [item for item in self.items.itervalues() if
                              item.type == equipment_type.id]
            items_for_type.sort(Equipment.compare_on_reassignment)
            for i, item in enumerate(items_for_type):
                item.in_type_index = i
        for instances in self.item_instances.itervalues():
            instances.item_ids.sort()


# TODO: Somehow share the logic with ShipPropertyFilter?
class EquipmentPropertyFilter(jsonobject.JSONSerializableObject):

    property = jsonobject.JSONProperty('property', value_type=unicode)
    """Property."""
    value = jsonobject.JSONProperty('value')
    """Value."""
    operator = jsonobject.JSONProperty('operator', value_type=int)
    """Operator."""
    OPERATOR_EQUAL = 0
    OPERATOR_NOT_EQUAL = 1
    OPERATOR_LESS_THAN = 2
    OPERATOR_LESS_THAN_EQUAL = 3
    OPERATOR_GREATER_THAN = 4
    OPERATOR_GREATER_THAN_EQUAL = 5
    OPERATOR_MAP = {
        OPERATOR_EQUAL: lambda a, b: a == b,
        OPERATOR_NOT_EQUAL: lambda a, b: a != b,
        OPERATOR_LESS_THAN: lambda a, b: a < b,
        OPERATOR_LESS_THAN_EQUAL: lambda a, b: a <= b,
        OPERATOR_GREATER_THAN: lambda a, b: a > b,
        OPERATOR_GREATER_THAN_EQUAL: lambda a, b: a >= b,
    }

    def apply(self, equipment, equipment_def_list):
        property_spec = self.property.encode('utf8').split('.')
        property_value = EquipmentPropertyFilter.get_property_value(
            equipment, property_spec, equipment_def_list)
        if property_value is None:
            return False
        operator = EquipmentPropertyFilter.OPERATOR_MAP.get(self.operator)
        if not operator:
            return False
        return operator(property_value, self.value)

    @staticmethod
    def get_property_value(target, property_spec, equipment_def_list):
        indirect_properties = [
            [(Equipment, 'definition'),
             lambda equipment: equipment.definition(equipment_def_list)],
        ]
        if not property_spec:
            return target
        if target is None:
            return None
        # Resolve the indirect property.
        for entry in indirect_properties:
            if (isinstance(target, entry[0][0]) and
                    property_spec[0] == entry[0][1]):
                return EquipmentPropertyFilter.get_property_value(
                    entry[1](target), property_spec[1:], equipment_def_list)
        # Get the normal property.
        if not hasattr(target, property_spec[0]):
            return None
        return EquipmentPropertyFilter.get_property_value(
            getattr(target, property_spec[0]), property_spec[1:],
            equipment_def_list)


class EquipmentTagFilter(jsonobject.JSONSerializableObject):
    pass


class EquipmentFilter(jsonobject.JSONSerializableObject):
    pass


class EquipmentPredicate(jsonobject.JSONSerializableObject):
    """Predicate for eqiupment selection.

    An equipment predicate is a notation to determine if a certain condition is
    met with the given equipment.

    Only one of the conditions if valid for one predicate at a time.
    """

    true_ = jsonobject.JSONProperty('true', value_type=bool)
    """TRUE condition.

    This predicate itself will be always true.
    """
    false_ = jsonobject.JSONProperty('false', value_type=bool)
    """FALSE condition.

    This predicate itself will be always false.
    """
    or_ = jsonobject.JSONProperty('or', value_type=list)
    """OR conditions.

    This predicate itself will be true if any of the child predicates is true.
    """
    and_ = jsonobject.JSONProperty('and', value_type=list)
    """AND conditions.

    This predicate itself will be true if all of the child predicates are true.
    """
    not_ = jsonobject.JSONProperty('not')
    """NOT condition.

    This predicate itself will be true if the child predicate is false.
    """
    property_filter = jsonobject.JSONProperty(
        'property_filter', value_type=EquipmentPropertyFilter)
    """Property filter.

    This predicate itself will be true if the given filter yields true."""
    tag_filter = jsonobject.JSONProperty(
        'tag_filter', value_type=EquipmentTagFilter)
    """Tag filter.

    This predicate itself will be true if the given tag is or is not contained.
    """
    filter = jsonobject.JSONProperty('filter', value_type=EquipmentFilter)
    """Ship filter.

    This predicate itself will be true if the given filter yields true."""

    def apply(self, equipment, equipment_def_list):
        """Apply the predicate to the given ship."""
        if self.true_:
            return True
        if self.false_:
            return False
        if self.or_:
            return any(or_.apply(equipment, equipment_def_list) for or_ in
                       self.or_)
        if self.and_:
            return all(and_.apply(equipment, equipment_def_list) for and_ in
                       self.and_)
        if self.not_:
            return not self.not_.apply(equipment, equipment_def_list)
        if self.property_filter:
            return self.property_filter.apply(equipment, equipment_def_list)
        if self.tag_filter:
            return self.tag_filter.apply(equipment, equipment_def_list)
        # TODO: Consider equipment filter.
        return True


# These value or element types cannot be set in the class body. Sounds like a
# flaw in language design...
# For now this hack resolves the issue.
EquipmentPredicate.or_._element_type = EquipmentPredicate
EquipmentPredicate.and_._element_type = EquipmentPredicate
EquipmentPredicate.not_._value_type = EquipmentPredicate


class EquipmentSorter(jsonobject.JSONSerializableObject):

    name = jsonobject.JSONProperty('name', value_type=unicode)
    """Name."""
    reversed = jsonobject.JSONProperty('reversed', value_type=bool)
    """Reversed or not.

    By default the sorter sorts equipments in ascending order of the metric
    that it cares about (i.e. from smallest to largest). When this property is
    true, the order is reversed (i.e. from largest to smallest).
    """

    def sort(self, equipments):
        if not self.name:
            return
        sorter = getattr(EquipmentSorter, self.name)
        equipments.sort(sorter, reverse=self.reversed)

    @staticmethod
    def definition(equipment_a, equipment_b):
        return Equipment.compare_on_reassignment(equipment_a, equipment_b)

    @staticmethod
    def powerup_score(equipment_a, equipment_b):
        return equipment_a.powerup_score - equipment_b.powerup_score


class EquipmentRequirement(jsonobject.JSONSerializableObject):

    target_slot = jsonobject.JSONProperty('target_slot', value_type=int)
    """Target slot type."""
    TARGET_SLOT_TOPMOST = 0
    TARGET_SLOT_LARGEST_AIRCRAFT_CAPACITY = 1
    predicate = jsonobject.JSONProperty('predicate',
                                        value_type=EquipmentPredicate)
    """Predicate."""
    sorter = jsonobject.JSONProperty('sorter', value_type=EquipmentSorter)
    """Sorter."""
    omittable = jsonobject.JSONProperty('omittable', False, value_type=bool)
    """Omittable.

    An omittable eqiupment can be omitted if a ship doesn't have a slot
    capacity to fit or no equipment is available for the given predicate."""

    def choose_slot_id(self, equipments, aircraft_slot_capacity):
        omittable_id = EquipmentDeploymentExpectation.EQUIPMENT_ID_OMITTABLE
        if self.target_slot == EquipmentRequirement.TARGET_SLOT_TOPMOST:
            return [pair[0] for pair in enumerate(equipments) if
                    pair[1].id == omittable_id][0]
        elif (self.target_slot ==
                EquipmentRequirement.TARGET_SLOT_LARGEST_AIRCRAFT_CAPACITY):
            pairs = [pair for pair in enumerate(aircraft_slot_capacity) if
                     equipments[pair[0]].id == omittable_id]
            pairs.sort(key=lambda pair: pair[1], reverse=True)
            return pairs[0][0]
        else:
            raise Exception('Invalid target slot: {}'.format(self.target_slot))


class EquipmentDeployment(jsonobject.JSONSerializableObject):

    ship_predicate = jsonobject.JSONProperty('ship_predicate',
                                             value_type=ship.ShipPredicate)
    """Ship predicate.

    A deployment can filter its scope with this predicate. Typically this is
    filter the ship type. For example, one can build a deployment for
    destroyers and another for aircraft battleships and combine both in one
    general deployment, and name as 'anti-submarine'.
    """
    requirements = jsonobject.JSONProperty(
        'requirements', value_type=list, element_type=EquipmentRequirement)
    """Equipment requirements.

    A deployment is considered not fit if any of requirement cannot be met.
    This may be due to insufficient slot capacity of a ship or unavailability
    of equipment.
    """

    def get_equipments(self, target_ship, equipment_pool, ship_def_list,
                       equipment_def_list):
        omittable_equipment = Equipment(
            id=EquipmentDeploymentExpectation.EQUIPMENT_ID_OMITTABLE)
        unavailable_equipment = Equipment(
            id=EquipmentDeploymentExpectation.EQUIPMENT_ID_UNAVAILABLE)
        equipments = [omittable_equipment] * target_ship.slot_count
        aircraft_slot_capacity = (
            target_ship.aircraft_slot_capacity[:target_ship.slot_count])
        loadable_types = (
            ship_def_list.ship_types[str(target_ship.ship_type)].
            loadable_equipment_types)
        equipment_pool = equipment_pool[:]
        num_placed = 0
        for requirement in self.requirements[:target_ship.slot_count]:
            if num_placed >= target_ship.slot_count:
                if requirement.omittable:
                    break
                return False, equipments
            slot_id = requirement.choose_slot_id(equipments,
                                                 aircraft_slot_capacity)
            applicable_equipments = [
                e for e in equipment_pool if
                loadable_types[str(e.type)] and
                requirement.predicate.apply(e, equipment_def_list)]
            requirement.sorter.sort(applicable_equipments)
            # For debuggig, it might be useful to uncomment the following.
#            for equipment in applicable_equipments:
#                definition = equipment.definition(equipment_def_list)
#                logger.debug(
#                    u'{} ({}): type {}, definition {}, in_type_index {}, '
#                    u'powerup_score {}'.format(
#                        definition.name, equipment.id, definition.type,
#                        definition.id, equipment.in_type_index,
#                        equipment.powerup_score))
            if not applicable_equipments:
                if not requirement.omittable:
                    equipments[slot_id] = unavailable_equipment
                    num_placed += 1
                # If it's omittable, just ignore this requirement and let the
                # next requirement decide.
            else:
                equipments[slot_id] = applicable_equipments[0]
                equipment_pool.remove(applicable_equipments[0])
                num_placed += 1
        possible = all([e.id != unavailable_equipment.id for e in equipments])
        omittable_seen = False
        for equipment in equipments:
            if omittable_seen and equipment.id > 0:
                possible = False
            omittable_seen = equipment.id == omittable_equipment.id
        return possible, equipments


class EquipmentGeneralDeployment(jsonobject.JSONSerializableObject):

    name = jsonobject.JSONProperty('name', value_type=unicode)
    """Name of the deployment."""
    deployments = jsonobject.JSONProperty(
        'deployments', value_type=list, element_type=EquipmentDeployment)
    """Deployments.

    Each deployment represents a specific deployment. If a ship tries to apply
    a general deployment, it actually applies the first deployment that fits to
    it. Those filtering may be done by the ship filter, or due to equipment
    availability."""


class EquipmentDeploymentExpectation(jsonobject.JSONSerializableObject):

    possible = jsonobject.JSONProperty('possible', value_type=bool)
    """True if it's possible to deploy."""
    ship_id = jsonobject.JSONProperty('ship_id', value_type=int)
    """Ship ID."""
    SHIP_ID_UNAVAILABLE = -1
    equipment_ids = jsonobject.JSONProperty('equipment_ids', value_type=list,
                                            element_type=int)
    """IDs of eqiupment.

    0 means an omittable equipment. -1 means it was required but nothing is
    available for the slot. This list is guaranteed to have the same length as
    the requirements field in the request.
    """
    EQUIPMENT_ID_OMITTABLE = 0
    EQUIPMENT_ID_UNAVAILABLE = -1


class EquipmentGeneralDeploymentExpectation(model.KCAARequestableObject):

    expectations = jsonobject.JSONProperty(
        'expectations', value_type=list,
        element_type=EquipmentDeploymentExpectation)
    """Expectations for each deployment."""

    @property
    def required_objects(self):
        return ['ShipDefinitionList', 'ShipList', 'EquipmentDefinitionList',
                'EquipmentList']

    def request(self, general_deployment, ship_definition_list, ship_list,
                equipment_definition_list, equipment_list):
        general_deployment = EquipmentGeneralDeployment.parse_text(
            general_deployment)
        ship_pool = ship_list.ships.values()
        equipment_pool = equipment_list.items.values()
        self.expectations = []
        for deployment in general_deployment.deployments:
            unavailable = EquipmentDeploymentExpectation(
                possible=False,
                ship_id=EquipmentDeploymentExpectation.SHIP_ID_UNAVAILABLE,
                equipment_ids=([
                    EquipmentDeploymentExpectation.EQUIPMENT_ID_UNAVAILABLE] *
                    len(deployment.requirements)))
            applicable_ships = [s for s in ship_pool if
                                deployment.ship_predicate.apply(s)]
            applicable_ships.sort(ship.ShipSorter.kancolle_level, reverse=True)
            if not applicable_ships:
                self.expectations.append(unavailable)
                continue
            found = False
            for target_ship in applicable_ships:
                possible, equipments = deployment.get_equipments(
                    target_ship, equipment_pool, ship_definition_list,
                    equipment_definition_list)
                if possible:
                    self.expectations.append(EquipmentDeploymentExpectation(
                        possible=True,
                        ship_id=target_ship.id,
                        equipment_ids=[e.id for e in equipments]))
                    found = True
                    break
            if not found:
                self.expectations.append(unavailable)
        return self
