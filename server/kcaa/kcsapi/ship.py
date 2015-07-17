#!/usr/bin/env python

import logging

import jsonobject
import model
import resource


# Loadable equipment types in addition to the default loadable map.
# There seems no data on this in the master data. Maintained manually.
# TODO: Revisit later. If there is considerable amount of this kind of data,
# KCSAPI master should contain them.
ADDITIONAL_LOADABLE_EQUIPMENT_TYPES = {
    131: [38],  # Yamato
    136: [38],  # Yamato Mk2
    143: [38],  # Musashi
    148: [38],  # Musashi Mk2
    178: [5],   # Bismarck drei
    275: [38],  # Nagato Mk2
    276: [38],  # Mutsu Mk2
}


logger = logging.getLogger('kcaa.kcsapi.ship')


class Variable(jsonobject.JSONSerializableObject):

    current = jsonobject.JSONProperty('current', value_type=int)
    """Current value."""
    baseline = jsonobject.JSONProperty('baseline', value_type=int)
    """Baseline value."""
    maximum = jsonobject.ReadonlyJSONProperty('maximum', value_type=int)
    """Maximum value."""

    @property
    def ratio(self):
        return float(self.current) / self.maximum

    @property
    def percentage(self):
        return int(100 * self.ratio)


class AbilityEnhancement(jsonobject.JSONSerializableObject):

    firepower = jsonobject.ReadonlyJSONProperty('firepower', value_type=int)
    """Firepower."""
    thunderstroke = jsonobject.ReadonlyJSONProperty('thunderstroke',
                                                    value_type=int)
    """Thunderstroke."""
    anti_air = jsonobject.ReadonlyJSONProperty('anti_air', value_type=int)
    """Anti-air."""
    armor = jsonobject.ReadonlyJSONProperty('armor', value_type=int)
    """Armor."""


class ShipDefinition(jsonobject.JSONSerializableObject):

    id = jsonobject.ReadonlyJSONProperty('id', value_type=int)
    """Ship definition ID."""
    name = jsonobject.ReadonlyJSONProperty('name', value_type=unicode)
    """Name."""
    ship_type = jsonobject.ReadonlyJSONProperty('ship_type', value_type=int)
    """Ship type."""
    SHIP_TYPE_COASTAL_DEFENSE_SHIP = 1
    SHIP_TYPE_DESTROYER = 2
    SHIP_TYPE_LIGHT_CRUISER = 3
    SHIP_TYPE_TORPEDO_CRUISER = 4
    SHIP_TYPE_HEAVY_CRUISER = 5
    SHIP_TYPE_AIRCRAFT_CRUISER = 6
    SHIP_TYPE_LIGHT_AIRCRAFT_CARRIER = 7
    SHIP_TYPE_LIGHT_BATTLESHIP = 8
    SHIP_TYPE_BATTLESHIP = 9
    SHIP_TYPE_AIRCRAFT_BATTLESHIP = 10
    SHIP_TYPE_AIRCRAFT_CARRIER = 11
    SHIP_TYPE_DREADNOUGHT_BATTLESHIP = 12
    SHIP_TYPE_SUBMARINE = 13
    SHIP_TYPE_SUBMARINE_AIRCRAFT_CARRIER = 14
    SHIP_TYPE_COMBAT_SUPPORT_SHIP = 15
    SHIP_TYPE_SEAPLANE_TENDER = 16
    SHIP_TYPE_LANDING_SHIP = 17
    SHIP_TYPE_ARMORED_AIRCRAFT_CARRIER = 18
    SHIP_TYPE_REPAIR_SHIP = 19
    SHIP_TYPE_SUBMARINE_TENDER = 20
    rarity = jsonobject.ReadonlyJSONProperty('rarity', value_type=int)
    """Rarity."""
    RARITY_UNKNOWN = 0
    RARITY_COMMON = 1  # Blue
    RARITY_FAMILIAR = 2  # Bluegreen
    RARITY_UNCOMMON = 3  # Silver
    RARITY_RARE = 4  # Golden
    RARITY_SUPER_RARE = 5  # Hologram
    RARITY_PRECIOUS = 6  # Shining hologram
    RARITY_DIVINE = 7  # Shining hologram
    resource_capacity = jsonobject.ReadonlyJSONProperty(
        'resource_capacity', value_type=resource.Resource)
    """Resource capacity."""
    armor = jsonobject.ReadonlyJSONProperty('armor', value_type=Variable)
    """Armor."""
    avoidance = jsonobject.ReadonlyJSONProperty('avoidance',
                                                value_type=Variable)
    """Avoidance."""
    firepower = jsonobject.ReadonlyJSONProperty('firepower',
                                                value_type=Variable)
    """Firepower."""
    thunderstroke = jsonobject.ReadonlyJSONProperty('thunderstroke',
                                                    value_type=Variable)
    """Thunderstroke."""
    anti_air = jsonobject.ReadonlyJSONProperty('anti_air', value_type=Variable)
    """Anti-air firepower."""
    anti_submarine = jsonobject.ReadonlyJSONProperty('anti_submarine',
                                                     value_type=Variable)
    """Anti-submarine firepower."""
    scouting = jsonobject.ReadonlyJSONProperty('scouting', value_type=Variable)
    """Scouting ability."""
    luck = jsonobject.ReadonlyJSONProperty('luck', value_type=Variable)
    """Luck."""
    aircraft_capacity = jsonobject.ReadonlyJSONProperty('aircraft_capacity',
                                                        value_type=int)
    """Aircraft capacity."""
    aircraft_slot_capacity = jsonobject.ReadonlyJSONProperty(
        'aircraft_slot_capacity', value_type=list, element_type=int)
    """Aircraft capacity for each slot."""
    speed = jsonobject.ReadonlyJSONProperty('speed', value_type=int)
    """Cruising speed."""
    # Seems like speed is not enum in the definition, but currently they are
    # practically an enum.
    SPEED_SLOW = 5
    SPEED_FAST = 10
    firing_range = jsonobject.ReadonlyJSONProperty('firing_range',
                                                   value_type=int)
    """Firing range."""
    FIRING_RANGE_SHORT = 1
    FIRING_RANGE_MIDDLE = 2
    FIRING_RANGE_LONG = 3
    FIRING_RANGE_VERY_LONG = 4
    slot_count = jsonobject.ReadonlyJSONProperty('slot_count', value_type=int)
    """Number of item slots."""
    build_time = jsonobject.ReadonlyJSONProperty('build_time', value_type=int)
    """Time required to build, in minutes."""
    upgrade_to = jsonobject.ReadonlyJSONProperty('upgrade_to', value_type=int)
    """Ship ID of the ship to which this ship can be upgraded."""
    upgrade_level = jsonobject.ReadonlyJSONProperty(
        'upgrade_level', value_type=int)
    """Ship level required to upgrade."""
    upgrade_resource = jsonobject.ReadonlyJSONProperty(
        'upgrade_resource', value_type=resource.Resource)
    """Resource required to upgrade."""
    upgrade_blueprints = jsonobject.ReadonlyJSONProperty(
        'upgrade_blueprints', value_type=int)
    """Blueprints required to upgrade."""
    rebuilding_material = jsonobject.ReadonlyJSONProperty(
        'rebuilding_material', value_type=AbilityEnhancement)
    """Rebuilding material."""
    additional_loadable_equipment_types = jsonobject.ReadonlyJSONProperty(
        'additional_loadable_equipment_types', [], value_type=list,
        element_type=int)
    """Equipment types loadable to this ship in addition to the default
    loadable equipment types for the belonging ship type."""
    sort_order = jsonobject.ReadonlyJSONProperty('sort_order', value_type=int)
    """Sort order, or the encyclopedia ID."""
    signature = jsonobject.JSONProperty('signature', value_type=int)
    """Ship signature.

    A ship signature is a unique ID of ships that share the same remodeling
    sequence. For example, if the ship model A can be upgraded to B, and B to
    C, then all of them are guaranteed to have the same ship signature.
    """

    def can_load(self, equipment_type, ship_def_list):
        if equipment_type in self.additional_loadable_equipment_types:
            return True
        ship_type_definition = ship_def_list.ship_types[str(self.ship_type)]
        return ship_type_definition.loadable_equipment_types[
            str(equipment_type)]

    @staticmethod
    def is_battleship(ship):
        return ship.ship_type in (
            ShipDefinition.SHIP_TYPE_LIGHT_BATTLESHIP,
            ShipDefinition.SHIP_TYPE_BATTLESHIP,
            ShipDefinition.SHIP_TYPE_AIRCRAFT_BATTLESHIP,
            ShipDefinition.SHIP_TYPE_DREADNOUGHT_BATTLESHIP)

    @staticmethod
    def is_heavy_cruiser(ship):
        return ship.ship_type in (
            ShipDefinition.SHIP_TYPE_HEAVY_CRUISER,
            ShipDefinition.SHIP_TYPE_AIRCRAFT_CRUISER)

    @staticmethod
    def is_light_cruiser(ship):
        return ship.ship_type in (
            ShipDefinition.SHIP_TYPE_LIGHT_CRUISER,
            ShipDefinition.SHIP_TYPE_TORPEDO_CRUISER)

    @staticmethod
    def is_aircraft_carrier(ship):
        # Submarine aircraft carrier is excluded here as its effect is limited.
        return ship.ship_type in (
            ShipDefinition.SHIP_TYPE_LIGHT_AIRCRAFT_CARRIER,
            ShipDefinition.SHIP_TYPE_AIRCRAFT_CARRIER,
            ShipDefinition.SHIP_TYPE_SEAPLANE_TENDER,
            ShipDefinition.SHIP_TYPE_ARMORED_AIRCRAFT_CARRIER)

    @staticmethod
    def is_submarine(ship):
        return ship.ship_type in (
            ShipDefinition.SHIP_TYPE_SUBMARINE,
            ShipDefinition.SHIP_TYPE_SUBMARINE_AIRCRAFT_CARRIER)

    @staticmethod
    def is_anti_submarine(ship):
        return ship.ship_type in (
            ShipDefinition.SHIP_TYPE_DESTROYER,
            ShipDefinition.SHIP_TYPE_LIGHT_CRUISER,
            ShipDefinition.SHIP_TYPE_TORPEDO_CRUISER,
            ShipDefinition.SHIP_TYPE_AIRCRAFT_CRUISER,
            ShipDefinition.SHIP_TYPE_LIGHT_AIRCRAFT_CARRIER,
            ShipDefinition.SHIP_TYPE_AIRCRAFT_BATTLESHIP)

    @property
    def rebuilding_rank(self):
        # Signature 402: Maru-Yu
        return (100 if self.signature == 402 else 0 +
                4 * self.rebuilding_material.anti_air +
                3 * self.rebuilding_material.firepower +
                2 * self.rebuilding_material.armor +
                1 * self.rebuilding_material.thunderstroke)


class ShipTypeDefinition(jsonobject.JSONSerializableObject):

    id = jsonobject.JSONProperty('id', value_type=int)
    """Ship type ID."""
    name = jsonobject.JSONProperty('name', value_type=unicode)
    """Ship type name."""
    loadable_equipment_types = jsonobject.JSONProperty(
        'loadable_equipment_types', {}, value_type=dict, element_type=bool)
    """Whether loadable or not for each eqiupment type."""
    sort_order = jsonobject.ReadonlyJSONProperty('sort_order', value_type=int)
    """Sort order, or the encyclopedia ID."""


class ShipDefinitionList(model.KCAAObject):
    """List of ship definitions."""

    ships = jsonobject.JSONProperty('ships', {}, value_type=dict,
                                    element_type=ShipDefinition)
    """Ships. Keyed by ship ID (string)."""
    ship_types = jsonobject.JSONProperty(
        'ship_types', {}, value_type=dict, element_type=ShipTypeDefinition)
    """Ship types. Keyed by ship type ID (string)."""

    def update(self, api_name, request, response, objects, debug):
        super(ShipDefinitionList, self).update(api_name, request, response,
                                               objects, debug)
        required_blueprints = {}
        for data in response.api_data.api_mst_shipupgrade:
            required_blueprints[data.api_id] = data.api_drawing_count
        for data in response.api_data.api_mst_ship:
            # Maps are always keyed by string in JSON, so it's safer to key
            # string here. This is required to make this object usable with
            # KCSAPI handler's serialization/deserialization mechanism.
            if data.api_id <= 500:
                # Player ships.
                self.ships[str(data.api_id)] = ShipDefinition(
                    id=data.api_id,
                    name=data.api_name,
                    ship_type=data.api_stype,
                    rarity=data.api_backs,
                    resource_capacity=resource.Resource(
                        fuel=data.api_fuel_max,
                        ammo=data.api_bull_max),
                    armor=Variable(
                        baseline=data.api_souk[0],
                        maximum=data.api_souk[1]),
                    firepower=Variable(
                        baseline=data.api_houg[0],
                        maximum=data.api_houg[1]),
                    thunderstroke=Variable(
                        baseline=data.api_raig[0],
                        maximum=data.api_raig[1]),
                    anti_air=Variable(
                        baseline=data.api_tyku[0],
                        maximum=data.api_tyku[1]),
                    luck=Variable(
                        baseline=data.api_luck[0],
                        maximum=data.api_luck[1]),
                    aircraft_capacity=sum(data.api_maxeq),
                    aircraft_slot_capacity=data.api_maxeq,
                    speed=data.api_soku,
                    firing_range=data.api_leng,
                    slot_count=data.api_slot_num,
                    build_time=data.api_buildtime,
                    upgrade_to=int(data.api_aftershipid),
                    upgrade_level=data.api_afterlv,
                    upgrade_resource=resource.Resource(
                        fuel=data.api_afterfuel,
                        ammo=data.api_afterbull),
                    upgrade_blueprints=required_blueprints.get(
                        int(data.api_aftershipid), 0),
                    rebuilding_material=AbilityEnhancement(
                        firepower=data.api_powup[0],
                        thunderstroke=data.api_powup[1],
                        anti_air=data.api_powup[2],
                        armor=data.api_powup[3]),
                    additional_loadable_equipment_types=(
                        ADDITIONAL_LOADABLE_EQUIPMENT_TYPES.get(
                            data.api_id, [])),
                    sort_order=data.api_sortno)
            else:
                # Enemy ships.
                self.ships[str(data.api_id)] = ShipDefinition(
                    id=data.api_id,
                    name=data.api_name,
                    ship_type=data.api_stype,
                    speed=data.api_soku,
                    slot_count=data.api_slot_num)
            # Unknown fields:
            #   api_houm: Fire hit probability? (HOUgeki Meichu)
            #   api_houk: Fire avoiding probability? (HOUgeki Kaihi)
            #   api_raim: Torpedo hit probability? (RAIgeki Meichu)
            #   api_raik: Torpedo avoiding probability? (RAIgeki Kaihi)
            #   api_atap, api_bakk, api_baku,
            #   api_enqflg, api_gumax, api_member_id,
            #   api_ndock_item, api_sakb, api_systems,
            #   api_touchs
            # Suspicious fields:
            #   api_broken: Required resources and time to repair?
            #     a: 1?
            #     b: coeff for repair time?
            #        repair time (sec) = lv * 5 * b * hp + 30
            #     c: ?
            #     d: ?
            #   api_cnum: Number in the ship class?
            #   api_ctype: Ship class?
            #   api_defeq: Default equipment?
            #   api_grow: Grown parameters? Should be valid only for owned
            #             ships.
            #   api_missions: Joining mission? Should be valid only for owned
            #                 ships.
            #   api_ndock_time: Only in member. Repair end time?
            #   api_onslot: Only in member. Number of aircrafts?
            #   api_sokuh: Only in master. Speed class? But as it's a
            #              a dependent variable only in master, I can't rely on
            #              it.
            #   api_srate: Only in member. The same as api_star?
            #   api_star: Only in member. The number of stars?
            # Ignored fields (known to be useless for KCAA):
            #   api_getmes, api_gomes, api_gomes2, api_homemes,
            #   api_ndock_time_str, api_sinfo, api_use_bull, api_use_fuel,
            #   api_voicef, api_yomi
            # Ability correspondence map (how redundant and complex!!)
            #   api_kaihi: api_kaih
            #   api_karyoku: api_houg (redundant)
            #   api_lucky: api_luck (redundant)
            #   api_raisou: api_raig (redundant)
            #   api_sakuteki: api_saku (redundant)
            #   api_soukou: api_souk (redundant)
            #   api_taiku: api_tyku (redundant)
            #   api_taisen: api_tais
        self.update_signatures()

        for data in response.api_data.api_mst_stype:
            self.ship_types[str(data.api_id)] = ShipTypeDefinition(
                id=data.api_id,
                name=data.api_name,
                loadable_equipment_types={
                    k: v != 0 for k, v in
                    data.api_equip_type.convert_to_dict().iteritems()},
                sort_order=data.api_sortno)

    def update_signatures(self):
        for ship in self.ships.itervalues():
            # Find the last ship in the remodeling sequence.
            last_ship = ship
            while last_ship.upgrade_to:
                last_ship = self.ships[str(last_ship.upgrade_to)]
            ship.signature = last_ship.id


class Ship(ShipDefinition):

    id = jsonobject.ReadonlyJSONProperty('id', value_type=int)
    """Instance ID."""
    ship_id = jsonobject.ReadonlyJSONProperty('ship_id', value_type=int)
    """Ship definition ID."""
    level = jsonobject.ReadonlyJSONProperty('level', value_type=int)
    """Level."""
    experience = jsonobject.ReadonlyJSONProperty('experience', value_type=int)
    """Experience point."""
    experience_next = jsonobject.ReadonlyJSONProperty(
        'experience_next', value_type=int)
    """Experience point needed to reach the next level."""
    experience_gauge = jsonobject.ReadonlyJSONProperty(
        'experience_gauge', value_type=int)
    """Percentage representing how many experience points collected in the
    current level."""
    hitpoint = jsonobject.ReadonlyJSONProperty('hitpoint', value_type=Variable)
    """Hit point (variable of hull durability)."""
    vitality = jsonobject.ReadonlyJSONProperty('vitality', value_type=int)
    """Vitality, or condition."""
    loaded_resource = jsonobject.ReadonlyJSONProperty(
        'loaded_resource', value_type=resource.Resource)
    """Currently loaded resource."""
    @jsonobject.jsonproperty
    def loaded_resource_percentage(self):
        """Currently loaded resource percentage.

        This property considers inaccurate fractions; for example, ship which
        consumed 30% of fuel out of capacity 15 would report it has 11 fuel
        units (it seems the server returns rounded number for 10.5). Assuming
        that the smallest resource unit is always 10% of the capacity, this
        property computes the nearest multiple of 10% given the
        :attr:`loaded_resource` and :attr:`resource_capacity`.
        """
        loaded = self.loaded_resource
        capacity = self.resource_capacity
        if not loaded or not capacity:
            return None
        return resource.ResourcePercentage(
            fuel=round(float(loaded.fuel) / capacity.fuel, 1),
            ammo=round(float(loaded.ammo) / capacity.ammo, 1))
    enhanced_ability = jsonobject.ReadonlyJSONProperty(
        'enhanced_ability', value_type=AbilityEnhancement)
    aircraft_slot_loaded = jsonobject.ReadonlyJSONProperty(
        'aircraft_slot_loaded', value_type=list, element_type=int)
    """Aircraft loaded for each slot."""
    equipment_ids = jsonobject.JSONProperty(
        'equipment_ids', value_type=list, element_type=int)
    """IDs of equipments."""
    """Enhanced ability by rebuilding or growth."""
    locked = jsonobject.JSONProperty('locked', value_type=bool)
    """True if this ship is locked."""
    unique = jsonobject.JSONProperty('unique', value_type=bool)
    """True if this ship is unique.

    A ship will be unique if:
    - it is the only ship which has its signature, or
    - it is the ship with highest level among ships that share the
      signature
    """
    is_under_repair = jsonobject.JSONProperty(
        'is_under_repair', value_type=bool)
    """True if the ship is under repair."""
    away_for_mission = jsonobject.JSONProperty(
        'away_for_mission', value_type=bool)
    """True if the ship is away for mission."""
    tags = jsonobject.JSONProperty(
        'tags', value_type=list, element_type=unicode)
    """Tags."""
    reserved_for_use = jsonobject.JSONProperty(
        'reserved_for_use', False, element_type=bool)
    """Whether reserved for use.

    A ship is marked as reserved for use when it is going on expedition,
    practice or mission. A ship reserved for use will not be in the ship pool
    when choosing another set of ships to use.
    """

    @property
    def ready(self):
        return (self.locked and
                not self.is_under_repair and
                not self.away_for_mission and
                not self.dangerous and
                self.vitality >= 30)

    @property
    def resource_full(self):
        return (self.loaded_resource.fuel == self.resource_capacity.fuel and
                self.loaded_resource.ammo == self.resource_capacity.ammo)

    @property
    def alive(self):
        return self.hitpoint.current > 0

    @property
    def dangerous(self):
        return self.hitpoint.ratio <= 0.5

    @property
    def fatal(self):
        return self.hitpoint.ratio <= 0.25

    @property
    def can_attack_midnight(self):
        return (not ShipDefinition.is_aircraft_carrier(self) and
                not self.fatal)


class ShipList(model.KCAAObject):
    """List of owned ship instances."""

    ships = jsonobject.JSONProperty('ships', {}, value_type=dict,
                                    element_type=Ship)
    """Ships. Keyed by instance ID (string)."""

    _prefs_loaded = False

    def get_ship_position(self, ship_id):
        if str(ship_id) not in self.ships:
            return None, None
        return self._compute_page_position(ship_id, sorted(
            self.ships.values(), ShipSorter.kancolle_level, reverse=True))

    @property
    def max_page(self):
        return (len(self.ships) + 9) / 10

    def rebuilding_enhanceable_ships(self, fleet_list):
        return [ship for ship in self.ships.itervalues() if
                ship.locked and not ship.is_under_repair and
                (not fleet_list.find_fleet_for_ship(ship.id) or
                 not fleet_list.find_fleet_for_ship(ship.id).mission_id)]

    def rebuilding_target_ships(self, fleet_list):
        return [ship for ship in self.ships.itervalues() if
                not fleet_list.find_fleet_for_ship(ship.id)]

    def get_ship_position_rebuilding_target(self, ship_id, fleet_list):
        if str(ship_id) not in self.ships:
            return None, None
        return self._compute_page_position(ship_id, sorted(
            self.rebuilding_target_ships(fleet_list),
            ShipSorter.kancolle_level))

    def rebuilding_available_material_ships(self, fleet_list):
        return [ship for ship in self.ships.itervalues() if
                not ship.locked and
                (not fleet_list.find_fleet_for_ship(ship.id) or
                 not fleet_list.find_fleet_for_ship(ship.id).mission_id) and
                not ship.unique]

    def rebuilding_material_ships(self, ship_ids_already_added=[]):
        return [ship for ship in self.ships.itervalues() if
                not ship.locked and ship.id not in ship_ids_already_added]

    def get_ship_position_rebuilding(self, ship_id, ship_ids_already_added):
        if str(ship_id) not in self.ships:
            return None, None
        return self._compute_page_position(ship_id, sorted(
            self.rebuilding_material_ships(ship_ids_already_added),
            ShipSorter.kancolle_level))

    def max_page_rebuilding(self, ship_ids_already_added):
        return (len(self.rebuilding_material_ships(ship_ids_already_added))
                + 9) / 10

    def damaged_ships(self):
        """Gets damaged ships.

        This does return ships under repair or away for mission.
        """
        return [ship for ship in self.ships.itervalues() if
                ship.hitpoint.ratio < 1]

    def repairable_ships(self, fleet_list):
        """Gets repairable ships.

        This does not include ships under repair or away for mission.
        """
        return [ship for ship in self.damaged_ships() if
                not ship.is_under_repair and
                (not fleet_list.find_fleet_for_ship(ship.id) or
                 not fleet_list.find_fleet_for_ship(ship.id).mission_id)]

    def get_ship_position_repair(self, ship_id, fleet_list):
        if str(ship_id) not in self.ships:
            return None, None
        return self._compute_page_position(ship_id, sorted(
            self.damaged_ships(),
            ShipSorter.hitpoint_ratio))

    def dissolvable_ships(self):
        """Gets dissolvable ships.

        This does not return ships under repair or away for mission.
        """
        return [ship for ship in self.ships.itervalues() if
                not ship.unique and
                not ship.locked and
                not ship.is_under_repair and
                not ship.away_for_mission]

    def _compute_page_position(self, ship_id, sorted_ships):
        sorted_ship_ids = [ship.id for ship in sorted_ships]
        ship_index = sorted_ship_ids.index(ship_id)
        page = 1 + ship_index / 10
        in_page_index = ship_index % 10
        return page, in_page_index

    def update(self, api_name, request, response, objects, debug):
        super(ShipList, self).update(api_name, request, response, objects,
                                     debug)
        if (api_name == '/api_port/port' or
                api_name == '/api_get_member/ship2'):
            if api_name == '/api_port/port':
                ship_data = response.api_data.api_ship
            elif api_name == '/api_get_member/ship2':
                ship_data = response.api_data
            updated_ids = set()
            for data in ship_data:
                ship = self.get_ship(data, objects).convert_to_dict()
                ShipList.update_ship(ship, data)
                self.ships[str(ship['id'])] = Ship(**ship)
                updated_ids.add(str(ship['id']))
            # Remove ships that have gone.
            for not_updated_id in set(self.ships.iterkeys()) - updated_ids:
                del self.ships[not_updated_id]
        elif api_name == '/api_get_member/ship3':
            # This is used with /api_req_kaisou/slotset and
            # /api_req_kaisou/remodeling.
            # When remodeling, ship3 only returns the updated ship, though as
            # a list.
            for data in response.api_data.api_ship_data:
                ship = self.get_ship(data, objects).convert_to_dict()
                ShipList.update_ship(ship, data)
                self.ships[str(ship['id'])] = Ship(**ship)
        elif api_name == '/api_req_hensei/lock':
            ship = self.ships[str(request.api_ship_id)]
            ship.locked = bool(response.api_data.api_locked)
        elif api_name == '/api_req_hokyu/charge':
            for ship_data in response.api_data.api_ship:
                ship = self.ships[str(ship_data.api_id)]
                ship.loaded_resource.fuel = ship_data.api_fuel
                ship.loaded_resource.ammo = ship_data.api_bull
        elif api_name == '/api_req_kaisou/remodeling':
            ship = self.ships[request.api_id]
            ship_defs = objects['ShipDefinitionList'].ships
            self.ships[str(ship.id)] = Ship(
                **ship_defs[str(ship.upgrade_to)].convert_to_dict())
        elif api_name == '/api_req_kaisou/powerup':
            ship_data = response.api_data.api_ship
            ship = self.ships[str(ship_data.api_id)].convert_to_dict()
            ShipList.update_ship(ship, ship_data)
            self.ships[str(ship['id'])] = Ship(**ship)
            # Remove material ships.
            for deleted_ship_id in request.api_id_items.split(','):
                del self.ships[deleted_ship_id]
        elif api_name == '/api_req_kousyou/destroyship':
            del self.ships[request.api_ship_id]
        elif api_name == '/api_req_kousyou/getship':
            ship = self.get_ship(response.api_data.api_ship,
                                 objects).convert_to_dict()
            ShipList.update_ship(ship, response.api_data.api_ship)
            self.ships[str(ship['id'])] = Ship(**ship)
        elif api_name == '/api_req_mission/start':
            # FleetList updates away_for_mission.
            pass
        elif api_name in ('/api_req_sortie/battle',
                          '/api_req_practice/battle',
                          '/api_req_combined_battle/battle',
                          '/api_req_combined_battle/battle_water'):
            self.update_battle(objects['Battle'], objects['FleetList'])
        elif api_name in ('/api_req_battle_midnight/battle',
                          '/api_req_practice/midnight_battle',
                          '/api_req_battle_midnight/sp_midnight',
                          '/api_req_combined_battle/midnight_battle',
                          '/api_req_combined_battle/sp_midnight'):
            self.update_midnight_battle(objects['MidnightBattle'],
                                        objects['FleetList'])
        elif api_name == '/api_get_member/deck':
            # FleetList updates away_for_mission.
            pass
        # Update is_under_repair.
        if api_name in ('/api_port/port',
                        '/api_get_member/ndock',
                        '/api_req_nyukyo/speedchange',
                        '/api_req_nyukyo/start'):
            self.update_is_under_repair(objects['RepairDock'])
        if (api_name == '/api_port/port' and not self._prefs_loaded and
                'Preferences' in objects):
            self.load_preferences(objects['Preferences'])
            self._prefs_loaded = True
        self.update_unique()

    def get_ship(self, ship_data, objects):
        try:
            return self.ships[str(ship_data.api_id)]
        except KeyError:
            ship_defs = objects['ShipDefinitionList'].ships
            return ship_defs[str(ship_data.api_ship_id)]

    @staticmethod
    def update_ship(ship, ship_data):
        ship.update({
            'id': ship_data.api_id,
            'ship_id': ship_data.api_ship_id,
            'level': ship_data.api_lv,
            'hitpoint': Variable(
                current=ship_data.api_nowhp,
                maximum=ship_data.api_maxhp),
            'vitality': ship_data.api_cond,
            'loaded_resource': resource.Resource(
                fuel=ship_data.api_fuel,
                ammo=ship_data.api_bull),
            # These ability parameters have correspondents in the ship
            # definition, but they are just the baseline values -- here we
            # populate the specific value to this ship instance.
            'armor': Variable(
                current=ship_data.api_soukou[0],
                baseline=ship['armor'].baseline,
                maximum=ship_data.api_soukou[1]),
            'avoidance': Variable(
                current=ship_data.api_kaihi[0],
                baseline=ship_data.api_kaihi[0],  # no baseline info
                maximum=ship_data.api_kaihi[1]),
            'firepower': Variable(
                current=ship_data.api_karyoku[0],
                baseline=ship['firepower'].baseline,
                maximum=ship_data.api_karyoku[1]),
            'thunderstroke': Variable(
                current=ship_data.api_raisou[0],
                baseline=ship['thunderstroke'].baseline,
                maximum=ship_data.api_raisou[1]),
            'anti_air': Variable(
                current=ship_data.api_taiku[0],
                baseline=ship['anti_air'].baseline,
                maximum=ship_data.api_taiku[1]),
            'anti_submarine': Variable(
                current=ship_data.api_taisen[0],
                baseline=ship_data.api_taisen[0],  # no baseline info
                maximum=ship_data.api_taisen[1]),
            'scouting': Variable(
                current=ship_data.api_sakuteki[0],
                baseline=ship_data.api_sakuteki[0],  # no baseline info
                maximum=ship_data.api_sakuteki[1]),
            'luck': Variable(
                current=ship_data.api_lucky[0],
                baseline=ship['luck'].baseline,
                maximum=ship_data.api_lucky[1]),
            'enhanced_ability': AbilityEnhancement(
                firepower=ship_data.api_kyouka[0],
                thunderstroke=ship_data.api_kyouka[1],
                anti_air=ship_data.api_kyouka[2],
                armor=ship_data.api_kyouka[3]),
            'aircraft_slot_loaded': ship_data.api_onslot,
            'equipment_ids': [id for id in ship_data.api_slot],
            'sort_order': ship_data.api_sortno})
        del ship['equipment_ids'][ship['slot_count']:]
        if hasattr(ship_data, 'api_backs'):
            ship['rarity'] = ship_data.api_backs
        # api_exp may be given as a list or a scalar.
        if isinstance(ship_data.api_exp, list):
            ship.update({
                'experience': ship_data.api_exp[0],
                'experience_next': ship_data.api_exp[1],
                'experience_gauge': ship_data.api_exp[2]})
        else:
            ship['experience'] = ship_data.api_exp
        if hasattr(ship_data, 'api_locked'):
            ship['locked'] = ship_data.api_locked != 0

    def update_is_under_repair(self, repair_dock):
        ship_ids_under_repair = frozenset(
            map(lambda slot: slot.ship_id, repair_dock.slots))
        for ship in self.ships.itervalues():
            ship.is_under_repair = ship.id in ship_ids_under_repair

    def update_battle(self, battle, fleet_list):
        fleet = fleet_list.fleets[battle.fleet_id - 1]
        ships = [self.ships[str(ship_id)] for ship_id in fleet.ship_ids]
        ShipList.deal_damage_in_phase(battle.aircraft_phase, ships)
        ShipList.deal_damage_in_phase(battle.opening_thunderstroke_phase,
                                      ships)
        for gunfire_phase in battle.gunfire_phases:
            ShipList.deal_damage_in_phase(gunfire_phase, ships)
        ShipList.deal_damage_in_phase(battle.thunderstroke_phase, ships)
        if battle.combined_fleet_id:
            combined_fleet = fleet_list.fleets[battle.combined_fleet_id - 1]
            combined_ships = [self.ships[str(ship_id)] for ship_id in
                              combined_fleet.ship_ids]
            ShipList.deal_damage_in_phase(battle.aircraft_phase_combined,
                                          combined_ships)
            ShipList.deal_damage_in_phase(battle.gunfire_phase_combined,
                                          combined_ships)
            ShipList.deal_damage_in_phase(battle.thunderstroke_phase_combined,
                                          combined_ships)

    def update_midnight_battle(self, battle, fleet_list):
        fleet = fleet_list.fleets[battle.fleet_id - 1]
        ships = [self.ships[str(ship_id)] for ship_id in fleet.ship_ids]
        ShipList.deal_damage_in_phase(battle.phase, ships)

    @staticmethod
    def deal_damage_in_phase(phase, ships):
        if not phase:
            return
        for attack in phase.attacks:
            if attack.attackee_lid > 6:
                continue
            attackee = ships[attack.attackee_lid - 1]
            attackee.hitpoint.current -= attack.damage

    def load_preferences(self, preferences):
        self.update_tags(preferences.ship_prefs.tags)

    def update_tags(self, tags):
        for ship_id, ship in self.ships.iteritems():
            if ship_id in tags:
                ship_tags = tags[ship_id]
                if ship_tags.tags != self.ships[ship_id].tags:
                    if ship.tags is None:
                        ship.tags = []
                    logger.debug(
                        u'Tags updated for ship {} ({}): [{}] -> [{}]'.format(
                            ship.name, ship.id,
                            u', '.join(tag for tag in ship.tags),
                            u', '.join(tag for tag in ship_tags.tags)))
                self.ships[ship_id].tags = ship_tags.tags
            elif ship.tags:
                logger.debug(u'Tags cleared for ship {} ({})'.format(
                    ship.name, ship.id))
                ship.tags = None
        # Optionally, it might be good to notify the user when a tag entry is
        # defined for a non-existent ship. That can be deleted automatically
        # when it is lost.

    def update_unique(self):
        signature_to_ships = {}
        for ship in self.ships.itervalues():
            ships = signature_to_ships.get(ship.signature, [])
            ships.append(ship)
            ships.sort(ShipSorter.kancolle_level, reverse=True)
            signature_to_ships[ship.signature] = ships
        for ship in self.ships.itervalues():
            ship.unique = signature_to_ships[ship.signature][0] is ship


class ShipPropertyFilter(jsonobject.JSONSerializableObject):

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

    def apply(self, ship):
        property_spec = self.property.encode('utf8').split('.')
        property_value = ShipPropertyFilter.get_property_value(
            ship, property_spec)
        if property_value is None:
            return False
        operator = ShipPropertyFilter.OPERATOR_MAP.get(self.operator)
        if not operator:
            return False
        return operator(property_value, self.value)

    @staticmethod
    def get_property_value(target, property_spec):
        if not property_spec:
            return target
        if target is None or not hasattr(target, property_spec[0]):
            return None
        return ShipPropertyFilter.get_property_value(
            getattr(target, property_spec[0]), property_spec[1:])


class ShipTagFilter(jsonobject.JSONSerializableObject):

    tag = jsonobject.JSONProperty('tag', value_type=unicode)
    """Tag."""
    operator = jsonobject.JSONProperty('operator', value_type=int)
    """Operator."""
    OPERATOR_CONTAINS = 0
    OPERATOR_NOT_CONTAINS = 1

    def apply(self, ship):
        if self.operator == ShipTagFilter.OPERATOR_CONTAINS:
            return ship.tags and self.tag in ship.tags
        if self.operator == ShipTagFilter.OPERATOR_NOT_CONTAINS:
            return not ship.tags or self.tag not in ship.tags
        return False


class ShipFilter(jsonobject.JSONSerializableObject):
    pass


class ShipPredicate(jsonobject.JSONSerializableObject):
    """Predicate for ship selection.

    A ship predicate is a notation to determine if a certain condition is met
    with the given ship.

    Only one of the conditions is valid for one predicate at a time.
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
        'property_filter', value_type=ShipPropertyFilter)
    """Property filter.

    This predicate itself will be true if the given filter yields true."""
    tag_filter = jsonobject.JSONProperty(
        'tag_filter', value_type=ShipTagFilter)
    """Tag filter.

    This predicate itself will be true if the given tag is or is not contained.
    """
    filter = jsonobject.JSONProperty('filter', value_type=ShipFilter)
    """Ship filter.

    This predicate itself will be true if the given filter yields true."""

    def apply(self, ship):
        """Apply the predicate to the given ship."""
        if self.true_:
            return True
        if self.false_:
            return False
        if self.or_:
            return any(or_.apply(ship) for or_ in self.or_)
        if self.and_:
            return all(and_.apply(ship) for and_ in self.and_)
        if self.not_:
            return not self.not_.apply(ship)
        if self.property_filter:
            return self.property_filter.apply(ship)
        if self.tag_filter:
            return self.tag_filter.apply(ship)
        # TODO: Consider ship filter.
        return True


# These value or element types cannot be set in the class body. Sounds like a
# flaw in language design...
# For now this hack resolves the issue.
ShipPredicate.or_._element_type = ShipPredicate
ShipPredicate.and_._element_type = ShipPredicate
ShipPredicate.not_._value_type = ShipPredicate


class ShipSorter(jsonobject.JSONSerializableObject):

    name = jsonobject.JSONProperty('name', value_type=unicode)
    """Name."""
    reversed = jsonobject.JSONProperty('reversed', value_type=bool)
    """Reversed or not.

    By default the sorter sorts ships in ascending order of the metric that it
    cares about (i.e. from smallest to largest). When this property is true,
    the order is reversed (i.e. from largest to smallest).
    """

    def sort(self, ships):
        if not self.name:
            return
        sorter = getattr(ShipSorter, self.name)
        ships.sort(sorter, reverse=self.reversed)

    @staticmethod
    def kancolle_level(ship_a, ship_b):
        # Note that this is reversed. When sorted by the level in descending
        # order, a ship with smaller sort_order comes first. Here we do the
        # reverse here.
        if ship_a.level != ship_b.level:
            return ship_a.level - ship_b.level
        if ship_a.sort_order != ship_b.sort_order:
            return -(ship_a.sort_order - ship_b.sort_order)
        return -(ship_a.id - ship_b.id)

    @staticmethod
    def hitpoint_ratio(ship_a, ship_b):
        if ship_a.hitpoint.ratio != ship_b.hitpoint.ratio:
            return cmp(ship_a.hitpoint.ratio, ship_b.hitpoint.ratio)
        # Non-damaged ships are sorted by the similar order as kancolle level.
        # Note that this is not reversed.
        if ship_a.sort_order != ship_b.sort_order:
            return ship_a.sort_order - ship_b.sort_order
        return ship_a.id - ship_b.id

    @staticmethod
    def rebuilding_rank(ship_a, ship_b):
        if ship_a.rebuilding_rank != ship_b.rebuilding_rank:
            return ship_a.rebuilding_rank - ship_b.rebuilding_rank
        return ShipSorter.kancolle_level(ship_a, ship_b)


class ShipRequirement(jsonobject.JSONSerializableObject):

    predicate = jsonobject.JSONProperty('predicate', value_type=ShipPredicate)
    """Predicate."""
    equipment_deployment = jsonobject.JSONProperty('equipment_deployment',
                                                   value_type=unicode)
    """Equipment deployment."""
    sorter = jsonobject.JSONProperty('sorter', value_type=ShipSorter)
    """Sorter."""
    omittable = jsonobject.JSONProperty('omittable', False, value_type=bool)
    """Omittable.

    An omittable ship can be omitted if no ship meets the condition required in
    the predicate. A slot with the omitted ship is filled up with the ships
    following that slot.
    """


class ShipIdList(model.KCAARequestableObject):

    ship_ids = jsonobject.JSONProperty('ship_ids', value_type=list,
                                       element_type=int)
    """IDs of ships to be loaded."""
