#!/usr/bin/env python

import jsonobject
import model


class GunfireHit(jsonobject.JSONSerializableObject):
    """Details of gunfire attack."""

    hit_type = jsonobject.JSONProperty('hit_type', value_type=int)
    """Hit type."""
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
        return [GunfireHit(hit_type=e[0], damage=int(e[1]), equipment=e[2])
                for e in zip(cl_list, damage, si_list)]


class GunfireAttack(jsonobject.JSONSerializableObject):
    """Details of gunfire attack."""

    attacker_lid = jsonobject.JSONProperty('attacker_lid', value_type=int)
    """Local ship ID of the attacker.

    Local ID represents the position of a ship. 1-6 represents the friend ships
    in the fleet, and 7-12 means the enemy ships."""
    attackee_lid = jsonobject.JSONProperty('attackee_lid', value_type=int)
    """Local ship ID of the attackee."""
    attack_type = jsonobject.JSONProperty('attack_type', value_type=int)
    """Attack type."""
    ATTACK_TYPE_GUNFIRE = 0
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
                damage=raigeki.api_fydam[i]))
        for i in xrange(1, len(raigeki.api_erai)):
            if raigeki.api_erai[i] == 0:
                continue
            attacks.append(ThunderstrokeAttack(
                attacker_lid=i + 6,
                attackee_lid=raigeki.api_erai[i],
                hit_type=raigeki.api_ecl[i],
                damage=raigeki.api_eydam[i]))
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
    gunfire_phases = jsonobject.JSONProperty('gunfire_phases', value_type=list,
                                             element_type=GunfirePhase)
    """Gunfire phases."""
    thunderstroke_phase = jsonobject.JSONProperty(
        'thunderstroke_phase', value_type=ThunderstrokePhase)
    """Thunderstroke phase."""

    def update(self, api_name, request, response, objects, debug):
        super(Battle, self).update(api_name, request, response, objects, debug)
        data = response.api_data
        self.fleet_id = data.api_dock_id
        self.gunfire_phases = []
        if data.api_hougeki1:
            self.gunfire_phases.append(GunfirePhase(
                attacks=GunfireAttack.create_list_from_hougeki(
                    data.api_hougeki1)))
        self.thunderstroke_phase = None
        if data.api_raigeki:
            self.thunderstroke_phase = ThunderstrokePhase(
                attacks=ThunderstrokeAttack.create_list_from_raigeki(
                    data.api_raigeki))

        # api_dock_id: fleet ID (typo of api_deck_id)
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
        #                  [1st hougeki, 2nd hougeki, 3rd hougeki,
        #                   thunderstroke]
        # api_kouku: aircraft fight
        #   api_plane_from: ship that released the planes?
        #   api_stage1: scouting phase
        #     api_disp_seiku: air supremacy result?
        #     api_e_count: number of aircrafts from enemy?
        #     api_e_lostcount: number of lost aircrafts from enemy?
        #     api_f_count: number of aircrafts from friend?
        #     api_f_lostcount: number of lost aircrafts from friend?
        #     api_touch_plane: scout contacting result?
        # api_maxhps: ship max hitpoints
        # api_midnight_flag: possibility of midnight battle
        # api_nowhps: ship current hitpoints (at the beginning)
        # api_opening_flag: the presence of opening thunderstroke phase?
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
        # api_ship_ke: ? (related to enemy ship equipment?)
        # api_ship_lv: enemy ship levels?
        # api_stage_flag: ?
        # api_support_flag: the presence of support fleet?


class MidnightBattle(model.KCAAObject):
    """Detailed information about the last midnight battle (expedition or
    practice)."""

    fleet_id = jsonobject.JSONProperty('fleet_id', value_type=int)
    """ID of the fleet which joined this battle."""
    phase = jsonobject.JSONProperty('phase', value_type=GunfirePhase)
    """Gunfire/thunderstroke phase."""

    def update(self, api_name, request, response, objects, debug):
        super(MidnightBattle, self).update(api_name, request, response,
                                           objects, debug)
        data = response.api_data
        self.fleet_id = int(data.api_deck_id)
        self.phase = GunfirePhase(
            attacks=GunfireAttack.create_list_from_hougeki(data.api_hougeki))
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
