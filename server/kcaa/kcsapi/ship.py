#!/usr/bin/env python

import jsonobject
import model
import resource


class Variable(jsonobject.JSONSerializableObject):

    current = jsonobject.JSONProperty('current', value_type=int)
    """Current value."""
    baseline = jsonobject.JSONProperty('baseline', value_type=int)
    """Baseline value."""
    maximum = jsonobject.ReadonlyJSONProperty('maximum', value_type=int)
    """Maximum value."""


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
    hull_durability = jsonobject.ReadonlyJSONProperty('hull_durability',
                                                      value_type=Variable)
    """Hull durability."""
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
    rebuilding_material = jsonobject.ReadonlyJSONProperty(
        'rebuilding_material', value_type=AbilityEnhancement)
    """Rebuilding material."""
    sort_order = jsonobject.ReadonlyJSONProperty('sort_order', value_type=int)
    """Sort order, or the dictionary ID."""


class ShipDefinitionList(model.KCAAObject):
    """List of ship definitions."""

    ships = jsonobject.JSONProperty('ships', {}, value_type=dict)
    """Ships. Keyed by ship ID."""
    # TODO: Needs key_type in jsonobject module.

    def update(self, api_name, response, objects):
        super(ShipDefinitionList, self).update(api_name, response, objects)
        for data in response['api_data']:
            ship_data = jsonobject.parse(data)
            # /api_get_master/ship KCSAPI returns empty results for unknown
            # ships. Those entries have a fuel capacity of 0.
            if ship_data.api_fuel_max == 0:
                continue
            self.ships[ship_data.api_id] = ShipDefinition(
                id=ship_data.api_id,
                name=ship_data.api_name,
                ship_type=ship_data.api_stype,
                rarity=ship_data.api_backs,
                resource_capacity=resource.Resource(
                    fuel=ship_data.api_fuel_max,
                    ammo=ship_data.api_bull_max),
                hull_durability=Variable(
                    baseline=ship_data.api_taik[0],
                    maximum=ship_data.api_taik[1]),
                armor=Variable(
                    baseline=ship_data.api_souk[0],
                    maximum=ship_data.api_souk[1]),
                avoidance=Variable(
                    baseline=ship_data.api_kaih[0],
                    maximum=ship_data.api_kaih[1]),
                firepower=Variable(
                    baseline=ship_data.api_houg[0],
                    maximum=ship_data.api_houg[1]),
                thunderstroke=Variable(
                    baseline=ship_data.api_raig[0],
                    maximum=ship_data.api_raig[1]),
                anti_air=Variable(
                    baseline=ship_data.api_tyku[0],
                    maximum=ship_data.api_tyku[1]),
                anti_submarine=Variable(
                    baseline=ship_data.api_tais[0],
                    maximum=ship_data.api_tais[1]),
                scouting=Variable(
                    baseline=ship_data.api_saku[0],
                    maximum=ship_data.api_saku[1]),
                luck=Variable(
                    baseline=ship_data.api_luck[0],
                    maximum=ship_data.api_luck[1]),
                aircraft_capacity=ship_data.api_tous[1],
                aircraft_slot_capacity=ship_data.api_maxeq,
                speed=ship_data.api_soku,
                firing_range=ship_data.api_leng,
                slot_count=ship_data.api_slot_num,
                build_time=ship_data.api_buildtime,
                upgrade_to=int(ship_data.api_aftershipid),
                upgrade_level=ship_data.api_afterlv,
                upgrade_resource=resource.Resource(
                    fuel=ship_data.api_afterfuel,
                    ammo=ship_data.api_afterbull),
                rebuilding_material=AbilityEnhancement(
                    firepower=ship_data.api_powup[0],
                    thunderstroke=ship_data.api_powup[1],
                    anti_air=ship_data.api_powup[2],
                    armor=ship_data.api_powup[3]),
                sort_order=ship_data.api_sortno)
            # Unknown fields:
            #   api_atap, api_bakk, api_baku,
            #   api_enqflg, api_gumax, api_houk, api_houm, api_ndock_item,
            #   api_raik, api_raim, api_sakb, api_systems, api_touchs
            # Suspicious fields:
            #   api_broken: Required resources and time to repair?
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
            #   api_slot: Only in member. Slot items?
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


class Ship(ShipDefinition):

    id = jsonobject.ReadonlyJSONProperty('id', value_type=int)
    """Instance ID."""
    ship_id = jsonobject.ReadonlyJSONProperty('ship_id', value_type=int)
    """Ship definition ID."""
    level = jsonobject.ReadonlyJSONProperty('level', value_type=int)
    """Level."""
    experience = jsonobject.ReadonlyJSONProperty('experience', value_type=int)
    """Experience point."""
    hitpoint = jsonobject.ReadonlyJSONProperty('hitpoint', value_type=Variable)
    """Hit point (variable of hull durability)."""
    vitality = jsonobject.ReadonlyJSONProperty('vitality', value_type=int)
    """Vitality, or condition."""
    loaded_resource = jsonobject.ReadonlyJSONProperty(
        'loaded_resource', value_type=resource.Resource)
    """Currently loaded resource."""
    enhanced_ability = jsonobject.ReadonlyJSONProperty(
        'enhanced_ability', value_type=AbilityEnhancement)
    """Enhanced ability by rebuilding or growth."""


class ShipList(model.KCAAObject):
    """List of owned ship instances."""

    ships = jsonobject.JSONProperty('ships', {}, value_type=dict)
    """Ships. Keyed by instanceID."""

    def update(self, api_name, response, objects):
        super(ShipList, self).update(api_name, response, objects)
        ship_defs = objects['ShipDefinitionList'].ships
        if api_name == '/api_get_member/ship':
            self.update_ships(response['api_data'], ship_defs)

    def update_ships(self, ships_data, ship_defs):
        updated_ids = set()
        for data in ships_data:
            ship_data = jsonobject.parse(data)
            ship_def = ship_defs[ship_data.api_ship_id].convert_to_dict()
            ship_def.update({
                'id': ship_data.api_id,
                'ship_id': ship_data.api_ship_id,
                'level': ship_data.api_lv,
                'experience': ship_data.api_exp,
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
                'hull_durability': Variable(
                    current=ship_data.api_taik[0],
                    baseline=ship_def['hull_durability'].baseline,
                    maximum=ship_data.api_taik[1]),
                'armor': Variable(
                    current=ship_data.api_soukou[0],
                    baseline=ship_def['armor'].baseline,
                    maximum=ship_data.api_soukou[1]),
                'avoidance': Variable(
                    current=ship_data.api_kaihi[0],
                    baseline=ship_def['avoidance'].baseline,
                    maximum=ship_data.api_kaihi[1]),
                'firepower': Variable(
                    current=ship_data.api_karyoku[0],
                    baseline=ship_def['firepower'].baseline,
                    maximum=ship_data.api_karyoku[1]),
                'thunderstroke': Variable(
                    current=ship_data.api_raisou[0],
                    baseline=ship_def['thunderstroke'].baseline,
                    maximum=ship_data.api_raisou[1]),
                'anti_air': Variable(
                    current=ship_data.api_taiku[0],
                    baseline=ship_def['anti_air'].baseline,
                    maximum=ship_data.api_taiku[1]),
                'anti_submarine': Variable(
                    current=ship_data.api_taisen[0],
                    baseline=ship_def['anti_submarine'].baseline,
                    maximum=ship_data.api_taisen[1]),
                'scouting': Variable(
                    current=ship_data.api_sakuteki[0],
                    baseline=ship_def['scouting'].baseline,
                    maximum=ship_data.api_sakuteki[1]),
                'luck': Variable(
                    current=ship_data.api_lucky[0],
                    baseline=ship_def['luck'].baseline,
                    maximum=ship_data.api_lucky[1]),
                'enhanced_ability': AbilityEnhancement(
                    firepower=ship_data.api_kyouka[0],
                    thunderstroke=ship_data.api_kyouka[1],
                    anti_air=ship_data.api_kyouka[2],
                    armor=ship_data.api_kyouka[0]),
                'sort_order': ship_data.api_sortno})
            self.ships[ship_def['id']] = Ship(**ship_def)
            updated_ids.add(ship_def['id'])
        # Remove ships that have gone.
        for not_updated_id in set(self.ships.iterkeys()) - updated_ids:
            del self.ships[not_updated_id]
