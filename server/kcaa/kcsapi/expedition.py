#!/usr/bin/env python

import jsonobject
import model


class Expedition(model.KCAAObject):
    """Information about the current expedition."""

    fleet_id = jsonobject.JSONProperty('fleet_id', value_type=int)
    """ID of the fleet which is going on expedition."""
    maparea_id = jsonobject.JSONProperty('maparea_id', value_type=int)
    """ID of the maparea."""
    map_id = jsonobject.JSONProperty('map_id', value_type=int)
    """ID of the map."""
    needs_compass = jsonobject.JSONProperty('needs_compass', value_type=bool)
    """Whether needs a compass on the next move."""
    cell_next = jsonobject.JSONProperty('cell_next', value_type=int)
    """ID of the next cell when the compass is determined.

    Cell ID is assigned from 0 (the start cell).
    Note that this is deterministically available when a compass is presented.
    """
    is_terminal = jsonobject.JSONProperty('is_terminal', value_type=bool)
    """Whether the next cell is the terminal of the path."""
    cell_boss = jsonobject.JSONProperty('cell_boss', value_type=int)
    """ID of the cell where a boss lives."""
    event = jsonobject.JSONProperty('event', value_type=int)
    """Event that will happen in the next cell."""
    EVENT_ITEM = 2
    EVENT_BATTLE = 4
    EVENT_BATTLE_BOSS = 5

    def update(self, api_name, request, response, objects, debug):
        super(Expedition, self).update(api_name, request, response, objects,
                                       debug)
        if (api_name == '/api_req_map/start' or
                api_name == '/api_req_map/next'):
            if api_name == '/api_req_map/start':
                self.fleet_id = int(request.api_deck_id)
                self.maparea_id = int(request.api_maparea_id)
                self.map_id = int(request.api_mapinfo_no)
            self.needs_compass = response.api_data.api_rashin_flg == 1
            # api_rashin_id might represent the animation pattern of the
            # compass. Not useful here anyways.
            self.cell_next = response.api_data.api_no
            self.is_terminal = response.api_data.api_next == 0
            self.cell_boss = response.api_data.api_bosscell_no
            self.event = response.api_data.api_event_id
            # Other potentially interesting data:
            # - api_color_no: probably identical to api_event_id
            # - api_event_kind: additional info on the event?
            # - api_production_kind: probably the category of the found item
            # - api_enemy: enemy info (useful if submarines)


class ExpeditionBattle(model.KCAAObject):
    """Progress of the expedition battle."""

    def update(self, api_name, request, response, objects, debug):
        super(ExpeditionBattle, self).update(api_name, request, response,
                                             objects, debug)
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


class ExpeditionMidnightBattle(model.KCAAObject):
    """Progress of the expedition midnight battle."""

    def update(self, api_name, request, response, objects, debug):
        super(ExpeditionMidnightBattle, self).update(
            api_name, request, response, objects, debug)
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


class ExpeditionResult(model.KCAAObject):
    """Result of the latest expedition battle."""

    got_ship = jsonobject.JSONProperty('got_ship', value_type=bool)
    """Whether got a ship as a reward."""
    new_ship_id = jsonobject.JSONProperty('new_ship_id', value_type=int)
    """Ship definition ID of the new ship."""

    def update(self, api_name, request, response, objects, debug):
        super(ExpeditionResult, self).update(api_name, request, response,
                                             objects, debug)
        if api_name == '/api_req_sortie/battleresult':
            self.got_ship = response.api_data.api_get_flag[1] == 1
            if self.got_ship:
                self.new_ship_id = response.api_data.api_get_ship.api_ship_id
            else:
                self.new_ship_id = None
