#!/usr/bin/env python

import jsonobject
import model


class Battle(model.KCAAObject):
    """Detailed information about the last battle (expedition or practice)."""

    def update(self, api_name, request, response, objects, debug):
        super(Battle, self).update(api_name, request, response, objects, debug)
        # api_dock_id: ?
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
        # api_hourai_flag: the presence of gunfire and thunderstroke phase?
        # api_kouku: aircraft fight
        #   api_plane_from: ship that released the planes?
        #   api_stage1: ?
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

    def update(self, api_name, request, response, objects, debug):
        super(MidnightBattle, self).update(api_name, request, response,
                                           objects, debug)
        # Mostly the same as ExpeditionBattle.
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
