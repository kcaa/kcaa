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

    ships = jsonobject.JSONProperty('ships', {}, value_type=dict,
                                    element_type=ShipDefinition)
    """Ships. Keyed by ship ID (string)."""

    def update(self, api_name, request, response, objects, debug):
        super(ShipDefinitionList, self).update(api_name, request, response,
                                               objects, debug)
        for data in response.api_data.api_mst_ship:
            # /api_get_master/ship KCSAPI returns empty results for unknown
            # ships. Those entries have a fuel capacity of 0.
            if data.api_fuel_max == 0:
                continue
            # Maps are always keyed by string in JSON, so it's safer to key
            # string here. This is required to make this object usable with
            # KCSAPI handler's serialization/deserialization mechanism.
            self.ships[str(data.api_id)] = ShipDefinition(
                id=data.api_id,
                name=data.api_name,
                ship_type=data.api_stype,
                rarity=data.api_backs,
                resource_capacity=resource.Resource(
                    fuel=data.api_fuel_max,
                    ammo=data.api_bull_max),
                hull_durability=Variable(
                    baseline=data.api_taik[0],
                    maximum=data.api_taik[1]),
                armor=Variable(
                    baseline=data.api_souk[0],
                    maximum=data.api_souk[1]),
                avoidance=Variable(
                    baseline=data.api_kaih[0],
                    maximum=data.api_kaih[1]),
                firepower=Variable(
                    baseline=data.api_houg[0],
                    maximum=data.api_houg[1]),
                thunderstroke=Variable(
                    baseline=data.api_raig[0],
                    maximum=data.api_raig[1]),
                anti_air=Variable(
                    baseline=data.api_tyku[0],
                    maximum=data.api_tyku[1]),
                anti_submarine=Variable(
                    baseline=data.api_tais[0],
                    maximum=data.api_tais[1]),
                scouting=Variable(
                    baseline=data.api_saku[0],
                    maximum=data.api_saku[1]),
                luck=Variable(
                    baseline=data.api_luck[0],
                    maximum=data.api_luck[1]),
                aircraft_capacity=data.api_tous[1],
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
                rebuilding_material=AbilityEnhancement(
                    firepower=data.api_powup[0],
                    thunderstroke=data.api_powup[1],
                    anti_air=data.api_powup[2],
                    armor=data.api_powup[3]),
                sort_order=data.api_sortno)
            # Unknown fields:
            #   api_atap, api_bakk, api_baku,
            #   api_enqflg, api_gumax, api_houk, api_houm, api_member_id,
            #   api_ndock_item, api_raik, api_raim, api_sakb, api_systems,
            #   api_touchs
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
        return resource.ResourcePercentage(
            fuel=round(float(loaded.fuel) / capacity.fuel, 1),
            ammo=round(float(loaded.ammo) / capacity.ammo, 1))
    enhanced_ability = jsonobject.ReadonlyJSONProperty(
        'enhanced_ability', value_type=AbilityEnhancement)
    """Enhanced ability by rebuilding or growth."""
    locked = jsonobject.JSONProperty('locked', value_type=bool)
    """True if this ship is locked."""


class ShipList(model.KCAAObject):
    """List of owned ship instances."""

    ships = jsonobject.JSONProperty('ships', {}, value_type=dict,
                                    element_type=Ship)
    """Ships. Keyed by instance ID (string)."""

    def update(self, api_name, request, response, objects, debug):
        super(ShipList, self).update(api_name, request, response, objects,
                                     debug)
        updated_ids = set()
        if (api_name == '/api_port/port' or
                api_name == '/api_get_member/ship2'):
            if api_name == '/api_port/port':
                ship_data = response.api_data.api_ship
            else:
                ship_data = response.api_data
            for data in ship_data:
                ship = self.get_ship(data, objects).convert_to_dict()
                ShipList.update_ship(ship, data)
                self.ships[str(ship['id'])] = Ship(**ship)
                updated_ids.add(str(ship['id']))
        elif api_name == '/api_req_hensei/lock':
            ship = self.ships[str(request.api_ship_id)]
            ship.locked = bool(response.api_data.api_locked)
            return
        elif api_name == '/api_req_hokyu/charge':
            for ship_data in response.api_data.api_ship:
                ship = self.ships[str(ship_data.api_id)]
                ship.loaded_resource.fuel = ship_data.api_fuel
                ship.loaded_resource.ammo = ship_data.api_bull
            return
        elif api_name == '/api_req_kaisou/remodeling':
            ship_defs = objects['ShipDefinitionList'].ships
            self.ships[str(request.api_id)] = (
                ship_defs[str(self.ships[str(request.api_id)].upgrade_to)])
            return
        elif api_name == '/api_req_kousyou/getship':
            ship_defs = objects['ShipDefinitionList'].ships
            self.ships[str(response.api_data.api_id)] = (
                ship_defs[str(response.api_data.api_ship_id)])
            return
        # Remove ships that have gone.
        for not_updated_id in set(self.ships.iterkeys()) - updated_ids:
            del self.ships[not_updated_id]

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
                baseline=ship['avoidance'].baseline,
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
                baseline=ship['anti_submarine'].baseline,
                maximum=ship_data.api_taisen[1]),
            'scouting': Variable(
                current=ship_data.api_sakuteki[0],
                baseline=ship['scouting'].baseline,
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
            'sort_order': ship_data.api_sortno})
        if hasattr(ship_data, 'backs'):
            ship['rarity'] = ship_data.backs
        if hasattr(ship_data, 'api_taik'):
            ship['hull_durability'] = Variable(
                current=ship_data.api_taik[0],
                baseline=ship['hull_durability'].baseline,
                maximum=ship_data.api_taik[1])
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
