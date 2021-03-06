#!/usr/bin/env python

import jsonobject
import model
import ship


def initialize_enemy_ships(data, ship_def_list):
    enemy_ships = []
    for i in xrange(1, len(data.api_ship_lv)):
        if data.api_ship_lv[i] == -1:
            continue
        definition = ship_def_list.ships[str(data.api_ship_ke[i])]
        enemy_ships.append(ship.Ship(
            ship_type=definition.ship_type,
            level=data.api_ship_lv[i],
            hitpoint=ship.Variable(
                current=data.api_nowhps[i + 6],
                maximum=data.api_maxhps[i + 6])))
    return enemy_ships


def deal_enemy_damage_in_phase(phase, ships):
    if not phase:
        return
    for attack in phase.attacks:
        if attack.attackee_lid < 7:
            continue
        attackee = ships[attack.attackee_lid - 7]
        attackee.hitpoint.current -= attack.damage


def expect_result(ships, enemy_ships):
    enemy_alive_ships = [s for s in enemy_ships if s.alive]
    friend_alive_ships = [s for s in ships if s.alive]
    if not enemy_alive_ships and friend_alive_ships == ships:
        return Battle.RESULT_S
    if len(enemy_ships) == 6 and len(enemy_alive_ships) <= 2:
        return Battle.RESULT_A
    if len(enemy_ships) < 6 and 2 * len(enemy_alive_ships) <= len(enemy_ships):
        return Battle.RESULT_A
    if not enemy_ships[0].alive:
        return Battle.RESULT_B
    # The rest of results (losses) are not of interest.
    return Battle.RESULT_C


class AircraftAttack(jsonobject.JSONSerializableObject):
    """Details of aircraft attack."""

    attackee_lid = jsonobject.JSONProperty('attackee_lid', value_type=int)
    """Local ship ID of the attackee.

    Local ID represents the position of a ship. 1-6 represents the friend ships
    in the fleet, and 7-12 means the enemy ships."""
    hit_type = jsonobject.JSONProperty('hit_type', value_type=int)
    """Hit type."""
    HIT_TYPE_NORMAL = 0
    damage = jsonobject.JSONProperty('damage', value_type=int)
    """Damage dealt."""

    @staticmethod
    def create_list_from_kouku(kouku):
        attacks = []
        for i in xrange(1, len(kouku.api_fdam)):
            if kouku.api_fdam[i] == 0:
                continue
            attacks.append(AircraftAttack(
                attackee_lid=i,
                hit_type=kouku.api_fcl_flag[i],
                damage=int(kouku.api_fdam[i])))
        # For the combined fleet, the response doesn't have a damage entry for
        # the enemies (as it's redundant).
        if hasattr(kouku, 'api_edam'):
            for i in xrange(1, len(kouku.api_edam)):
                if kouku.api_edam[i] == 0:
                    continue
                attacks.append(AircraftAttack(
                    attackee_lid=i + 6,
                    hit_type=kouku.api_ecl_flag[i],
                    damage=int(kouku.api_edam[i])))
        return attacks


class AircraftPhase(jsonobject.JSONSerializableObject):
    """Details of aircraft battle phase."""

    attacks = jsonobject.JSONProperty('attacks', value_type=list,
                                      element_type=AircraftAttack)
    """Aircraft attacks, ordered arbitrarily."""


class SupportAttack(jsonobject.JSONSerializableObject):
    """Details of support attack."""

    attackee_lid = jsonobject.JSONProperty('attackee_lid', value_type=int)
    """Local ship ID of the attackee.

    Local ID represents the position of a ship. 1-6 represents the friend ships
    in the fleet, and 7-12 means the enemy ships."""
    hit_type = jsonobject.JSONProperty('hit_type', value_type=int)
    """Hit type."""
    HIT_TYPE_MISS = 0
    HIT_TYPE_HIT = 1
    HIT_TYPE_CRITICAL = 2
    damage = jsonobject.JSONProperty('damage', value_type=int)
    """Damage dealt."""

    @staticmethod
    def create_list_from_hourai(hourai):
        attacks = []
        for i in xrange(1, len(hourai.api_damage)):
            if hourai.api_damage[i] == 0:
                continue
            attacks.append(SupportAttack(
                attackee_lid=i + 6,
                hit_type=hourai.api_cl_list[i],
                damage=int(hourai.api_damage[i])))
        return attacks


class SupportPhase(jsonobject.JSONSerializableObject):
    """Details of support fleet attack phase."""
    # NOTE: Currently only the gunfire support is supported.
    # TODO: Support the aircraft support and thunderstroke support as well.

    type = jsonobject.JSONProperty('type', value_type=int)
    TYPE_GUNFIRE = 2
    attacks = jsonobject.JSONProperty('attacks', value_type=list,
                                      element_type=SupportAttack)
    """Support attacks, ordered arbitrarily."""

    @staticmethod
    def create_from_data(flag, data):
        if flag == SupportPhase.TYPE_GUNFIRE:
            return SupportPhase(
                type=SupportPhase.TYPE_GUNFIRE,
                attacks=SupportAttack.create_list_from_hourai(
                    data.api_support_hourai))


class GunfireHit(jsonobject.JSONSerializableObject):
    """Details of gunfire attack."""

    hit_type = jsonobject.JSONProperty('hit_type', value_type=int)
    """Hit type."""
    HIT_TYPE_NO_ATTACK = -1
    HIT_TYPE_MISS = 0
    HIT_TYPE_HIT = 1
    HIT_TYPE_CRITICAL = 2
    damage = jsonobject.JSONProperty('damage', value_type=int)
    """Damage dealt."""
    equipment = jsonobject.JSONProperty('equipment', value_type=int)
    """Equipment used."""

    @staticmethod
    def create_list_from_hougeki(cl_list, damage, si_list):
        # damage list sometimes contains rounding errors?
        hits = []
        for e in zip(cl_list, damage, si_list):
            hits.append(GunfireHit(
                hit_type=e[0],
                damage=int(e[1]) if e[0] >= GunfireHit.HIT_TYPE_HIT else 0,
                equipment=e[2]))
        return hits


class GunfireAttack(jsonobject.JSONSerializableObject):
    """Details of gunfire attack."""

    attacker_lid = jsonobject.JSONProperty('attacker_lid', value_type=int)
    """Local ship ID of the attacker.

    Local ID represents the position of a ship. 1-6 represents the friend ships
    in the fleet, and 7-12 means the enemy ships.
    """
    attackee_lid = jsonobject.JSONProperty('attackee_lid', value_type=int)
    """Local ship ID of the attackee."""
    attack_type = jsonobject.JSONProperty('attack_type', value_type=int)
    """Attack type."""
    ATTACK_TYPE_NORMAL = 0
    ATTACK_TYPE_SCOUT_FEEDBACK = 2
    hits = jsonobject.JSONProperty('hits', value_type=list,
                                   element_type=GunfireHit)
    """Hits of this attack."""

    @property
    def damage(self):
        return sum(hit.damage for hit in self.hits)

    @staticmethod
    def create_list_from_hougeki(hougeki):
        attacks = []
        for i in xrange(1, len(hougeki.api_at_list)):
            # api_df_list takes a list for each attack. Maybe there is a future
            # plan that 2 attacks in a row can attack a different ship for each
            # hit?
            attack = GunfireAttack(
                attacker_lid=hougeki.api_at_list[i],
                attackee_lid=hougeki.api_df_list[i][0],
                hits=GunfireHit.create_list_from_hougeki(
                    hougeki.api_cl_list[i],
                    hougeki.api_damage[i],
                    hougeki.api_si_list[i]))
            # api_at_type is not present if called from MidnightBattle.
            if hasattr(hougeki, 'api_at_type'):
                attack.attack_type = hougeki.api_at_type[i]
            attacks.append(attack)
        return attacks


class GunfirePhase(jsonobject.JSONSerializableObject):
    """Details of gunfire battle phase."""

    attacks = jsonobject.JSONProperty('attacks', value_type=list,
                                      element_type=GunfireAttack)
    """Gunfire attacks, ordered chronologically."""


class ThunderstrokeAttack(jsonobject.JSONSerializableObject):
    """Details of thunderstroke attack."""

    attacker_lid = jsonobject.JSONProperty('attacker_lid', value_type=int)
    """Local ship ID of the attacker.

    Local ID represents the position of a ship. 1-6 represents the friend ships
    in the fleet, and 7-12 means the enemy ships."""
    attackee_lid = jsonobject.JSONProperty('attackee_lid', value_type=int)
    """Local ship ID of the attackee."""
    hit_type = jsonobject.JSONProperty('hit_type', value_type=int)
    """Hit type."""
    HIT_TYPE_MISS = 0
    HIT_TYPE_HIT = 1
    HIT_TYPE_CRITICAL = 2
    damage = jsonobject.JSONProperty('damage', value_type=int)
    """Damage dealt."""

    @staticmethod
    def create_list_from_raigeki(raigeki):
        attacks = []
        for i in xrange(1, len(raigeki.api_frai)):
            if raigeki.api_frai[i] == 0:
                continue
            # raigeki.api_fdam is the damage suffered from enemy attacks, which
            # is redundant information.
            attacks.append(ThunderstrokeAttack(
                attacker_lid=i,
                attackee_lid=raigeki.api_frai[i] + 6,
                hit_type=raigeki.api_fcl[i],
                damage=int(raigeki.api_fydam[i])))
        for i in xrange(1, len(raigeki.api_erai)):
            if raigeki.api_erai[i] == 0:
                continue
            attacks.append(ThunderstrokeAttack(
                attacker_lid=i + 6,
                attackee_lid=raigeki.api_erai[i],
                hit_type=raigeki.api_ecl[i],
                damage=int(raigeki.api_eydam[i])))
        return attacks


class ThunderstrokePhase(jsonobject.JSONSerializableObject):
    """Details of thunderstroke battle phase."""

    attacks = jsonobject.JSONProperty('attacks', value_type=list,
                                      element_type=ThunderstrokeAttack)
    """Thunderstroke attacks, ordered arbitrarily."""


class Battle(model.KCAAObject):
    """Detailed information about the last battle (expedition or practice)."""

    fleet_id = jsonobject.JSONProperty('fleet_id', value_type=int)
    """ID of the fleet which joined this battle."""
    combined_fleet_id = jsonobject.JSONProperty('combined_fleet_id',
                                                value_type=int)
    """ID of the combined fleet which joined this battle. Can be None if this
    is a usual battle."""
    aircraft_phase = jsonobject.JSONProperty(
        'aircraft_phase', value_type=AircraftPhase)
    """Aircraft phase."""
    aircraft_phase_combined = jsonobject.JSONProperty(
        'aircraft_phase_combined', value_type=AircraftPhase)
    """Aircraft phase for the combined fleet."""
    support_phase = jsonobject.JSONProperty(
        'support_phase', value_type=SupportPhase)
    """Support phase from the supporting fleet."""
    opening_thunderstroke_phase = jsonobject.JSONProperty(
        'opening_thunderstroke_phase', value_type=ThunderstrokePhase)
    """Opening thunderstroke phase."""
    gunfire_phases = jsonobject.JSONProperty('gunfire_phases', value_type=list,
                                             element_type=GunfirePhase)
    """Gunfire phases."""
    gunfire_phase_combined = jsonobject.JSONProperty(
        'gunfire_phase_combined', value_type=GunfirePhase)
    """Gunfire phase for the combined fleet."""
    thunderstroke_phase = jsonobject.JSONProperty(
        'thunderstroke_phase', value_type=ThunderstrokePhase)
    """Thunderstroke phase."""
    thunderstroke_phase_combined = jsonobject.JSONProperty(
        'thunderstroke_phase_combined', value_type=ThunderstrokePhase)
    """Thunderstroke phase for the combined fleet."""
    need_midnight_battle = jsonobject.JSONProperty(
        'need_midnight_battle', value_type=bool)
    """Whether to need a midnight battle to fully defeat the enemy."""
    enemy_ships = jsonobject.JSONProperty(
        'enemy_ships', value_type=list, element_type=ship.Ship)
    """Enemy ships."""

    RESULT_E = 1
    RESULT_D = 2
    RESULT_C = 3
    RESULT_B = 4
    RESULT_A = 5
    RESULT_S = 6

    @staticmethod
    def get_result_for_win_rank(win_rank):
        return {
            'E': Battle.RESULT_E,
            'D': Battle.RESULT_D,
            'C': Battle.RESULT_C,
            'B': Battle.RESULT_B,
            'A': Battle.RESULT_A,
            'S': Battle.RESULT_S,
        }[win_rank]

    def update(self, api_name, request, response, objects, debug):
        super(Battle, self).update(api_name, request, response, objects, debug)
        ship_def_list = objects['ShipDefinitionList']
        data = response.api_data
        if api_name in ('/api_req_sortie/battle',
                        '/api_req_practice/battle'):
            self.fleet_id = data.api_dock_id
            self.combined_fleet_id = None
        elif api_name in ('/api_req_combined_battle/battle',
                          '/api_req_combined_battle/battle_water'):
            self.fleet_id = 1
            self.combined_fleet_id = 2
        else:
            raise Exception('Unexpected API: {}'.format(api_name))
        begin_with_combined = api_name == '/api_req_combined_battle/battle'
        # Aircraft attack phase.
        self.aircraft_phase = None
        if data.api_kouku.api_stage3:
            self.aircraft_phase = AircraftPhase(
                attacks=AircraftAttack.create_list_from_kouku(
                    data.api_kouku.api_stage3))
        self.aircraft_phase_combined = None
        if (hasattr(data.api_kouku, 'api_stage3_combined') and
                data.api_kouku.api_stage3_combined):
            self.aircraft_phase_combined = AircraftPhase(
                attacks=AircraftAttack.create_list_from_kouku(
                    data.api_kouku.api_stage3_combined))
        # Maybe api_support_flag is useful for detection?
        if hasattr(data, 'api_support_info'):
            self.support_phase = SupportPhase.create_from_data(
                data.api_support_flag, data.api_support_info)
        # Opening thunderstroke phase.
        # TODO: Check if the target of enemy's thunderstrokes are really the
        # main fleet.
        self.opening_thunderstroke_phase = None
        if data.api_opening_flag != 0:
            self.opening_thunderstroke_phase = ThunderstrokePhase(
                attacks=ThunderstrokeAttack.create_list_from_raigeki(
                    data.api_opening_atack))
        # Detect the attack phases.
        main_hougekis = []
        main_raigeki = None
        combined_hougeki = None
        combined_raigeki = None
        if not self.combined_fleet_id:
            # For usual battles.
            main_hougekis = []
            if data.api_hourai_flag[0] != 0:
                main_hougekis.append(data.api_hougeki1)
            if data.api_hourai_flag[1] != 0:
                main_hougekis.append(data.api_hougeki2)
            # Seems like api_hourai_flag[2] is always 0.
            if data.api_hourai_flag[3] != 0:
                main_raigeki = data.api_raigeki
        elif not begin_with_combined:
            # For combined surface fleet battles.
            main_hougekis = []
            if data.api_hourai_flag[0] != 0:
                main_hougekis.append(data.api_hougeki1)
            if data.api_hourai_flag[1] != 0:
                main_hougekis.append(data.api_hougeki2)
            if data.api_hourai_flag[2] != 0:
                combined_hougeki = data.api_hougeki3
            if data.api_hourai_flag[3] != 0:
                combined_raigeki = data.api_raigeki
        else:
            # For combined mobile fleet battles.
            if data.api_hourai_flag[0] != 0:
                combined_hougeki = data.api_hougeki1
            if data.api_hourai_flag[1] != 0:
                combined_raigeki = data.api_raigeki
            if data.api_hourai_flag[2] != 0:
                main_hougekis.append(data.api_hougeki2)
            if data.api_hourai_flag[3] != 0:
                main_hougekis.append(data.api_hougeki3)
        # Gunfire phases.
        self.gunfire_phases = (
            [GunfirePhase(
                attacks=GunfireAttack.create_list_from_hougeki(hougeki))
             for hougeki in main_hougekis])
        self.gunfire_phase_combined = None
        if combined_hougeki:
            self.gunfire_phase_combined = GunfirePhase(
                attacks=GunfireAttack.create_list_from_hougeki(
                    combined_hougeki))
        # Thunderstroke phase.
        self.thunderstroke_phase = None
        if main_raigeki:
            self.thunderstroke_phase = ThunderstrokePhase(
                attacks=ThunderstrokeAttack.create_list_from_raigeki(
                    main_raigeki))
        self.thunderstroke_phase_combined = None
        if combined_raigeki:
            self.thunderstroke_phase_combined = ThunderstrokePhase(
                attacks=ThunderstrokeAttack.create_list_from_raigeki(
                    combined_raigeki))
        self.need_midnight_battle = data.api_midnight_flag != 0
        self.update_enemy_ships(data, ship_def_list)

        # api_dock_id: fleet ID (note: typo on deck)
        # api_eKyouka: enemy enhanced parameters?
        # api_eParam: enemy current parameters (4 primary values)
        # api_eSlot: enemy equipments
        # api_fParam: friend current parameters (4 primary values)
        # api_formation: formation? (friend, enemy, ?)
        # api_hougeki1: gunfire 1st round
        #   api_at_list: attack order list (1-6: friend, 7-12: enemy)
        #   api_at_type: attack type? (0: gunfire, ...)
        #   api_cl_list: hit? (0: miss, 1: hit, 2: critical hit)
        #                the list has 2 items if 2 attacks in a row
        #   api_damage: damage dealt in the attack
        #   api_df_list: attack target (1-6: friend, 7-12: enemy)
        #   api_si_list: equipment used
        # api_hourai_flag: the presence of phases
        #                  [1st hougeki, 2nd hougeki,
        #                   3rd hougeki (for the combined fleet),
        #                   thunderstroke (of the combined fleet if any)]
        # api_kouku: aircraft fight
        #   api_plane_from: ship that released the planes?
        #   api_stage1: scouting phase
        #     api_disp_seiku: air supremacy result?
        #     api_e_count: number of aircrafts from enemy?
        #     api_e_lostcount: number of lost aircrafts from enemy?
        #     api_f_count: number of aircrafts from friend?
        #     api_f_lostcount: number of lost aircrafts from friend?
        #     api_touch_plane: scout contacting result?
        #   api_stage2: anti air gunfire phase
        #     api_e_count: number of aircrafts from enemy?
        #     api_e_lostcount: number of lost aircrafts from enemy?
        #     api_f_count: number of aircrafts from friend?
        #     api_f_lostcount: number of lost aircrafts from friend?
        #   api_stage3: attack aircraft and dive bomber phase
        #     api_ebak_flag: enemy bomber affected ships
        #     api_ecl_flag: enemy hit types
        #     api_edam: enemy suffered damage
        #     api_erai_flag: enemy attacker affected ships
        #     api_f*: same for friend
        #   api_stage3_combined: the same for combined fleet, without api_e*
        # api_maxhps: ship max hitpoints
        # api_midnight_flag: possibility of midnight battle
        # api_nowhps: ship current hitpoints (at the beginning)
        # api_opening_flag: the presence of opening thunderstroke phase?
        # api_opening_atack: opening thunderstroke fight (note: typo on attack)
        # api_raigeki: thunderstroke fight
        #   api_ecl: hit? (0: miss, 1: hit, 2: critical hit)
        #   api_edam: damage that enemy suffered
        #   api_erai: target of thunderstroke attack (0: no attack)
        #   api_eydam: damage dealt to friend
        #   api_fcl: hit?
        #   api_fdam: damage that friend suffered
        #   api_frai: target of thunderstroke attack (1-6: enemy)
        #   api_fydam: damage dealt to enemy
        # api_search: aircraft scout?
        # api_ship_ke: ? (related to enemy ship type or equipment?)
        # api_ship_lv: enemy ship levels?
        # api_stage_flag: ?
        # api_support_flag: the presence of support fleet?

    def update_enemy_ships(self, data, ship_def_list):
        self.enemy_ships = initialize_enemy_ships(data, ship_def_list)
        deal_enemy_damage_in_phase(self.aircraft_phase, self.enemy_ships)
        deal_enemy_damage_in_phase(self.aircraft_phase_combined,
                                   self.enemy_ships)
        deal_enemy_damage_in_phase(self.support_phase, self.enemy_ships)
        deal_enemy_damage_in_phase(self.opening_thunderstroke_phase,
                                   self.enemy_ships)
        for gunfire_phase in self.gunfire_phases:
            deal_enemy_damage_in_phase(gunfire_phase, self.enemy_ships)
        deal_enemy_damage_in_phase(self.gunfire_phase_combined,
                                   self.enemy_ships)
        deal_enemy_damage_in_phase(self.thunderstroke_phase, self.enemy_ships)
        deal_enemy_damage_in_phase(self.thunderstroke_phase_combined,
                                   self.enemy_ships)


class MidnightBattle(model.KCAAObject):
    """Detailed information about the last midnight battle (expedition or
    practice)."""

    fleet_id = jsonobject.JSONProperty('fleet_id', value_type=int)
    """ID of the fleet which joined this battle."""
    phase = jsonobject.JSONProperty('phase', value_type=GunfirePhase)
    """Gunfire/thunderstroke phase."""
    enemy_ships = jsonobject.JSONProperty(
        'enemy_ships', value_type=list, element_type=ship.Ship)
    """Enemy ships."""

    def update(self, api_name, request, response, objects, debug):
        super(MidnightBattle, self).update(api_name, request, response,
                                           objects, debug)
        ship_def_list = objects['ShipDefinitionList']
        data = response.api_data
        if api_name in ('/api_req_combined_battle/midnight_battle',
                        '/api_req_combined_battle/sp_midnight'):
            # The combined fleet will always join the midnight battle.
            self.fleet_id = 2
        else:
            self.fleet_id = int(data.api_deck_id)
        self.phase = GunfirePhase(
            attacks=GunfireAttack.create_list_from_hougeki(data.api_hougeki))
        self.update_enemy_ships(data, ship_def_list)
        # Mostly the same as ExpeditionBattle.
        # api_deck_id: same
        # api_eKyouka: same
        # api_eParam: same
        # api_eSlot: same
        # api_fParam: same
        # api_flare_pos: position of ship with search light?
        # api_hougeki: gunfire and thunderstroke
        #   api_at_list: attack order list
        #   api_cl_list: hit? (2 items in the list if 2 attacks in a row)
        #   api_damage: damage dealt
        #   api_df_list: attack target
        #   api_si_list: equipment used
        #   api_sp_list: presence of special attack?
        # api_maxhps: same
        # api_nowhps: same
        # api_ship_ke: same?
        # api_ship_lv: same
        # api_touch_plane: clutter?

    def update_enemy_ships(self, data, ship_def_list):
        self.enemy_ships = initialize_enemy_ships(data, ship_def_list)
        deal_enemy_damage_in_phase(self.phase, self.enemy_ships)
