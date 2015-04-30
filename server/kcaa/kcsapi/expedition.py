#!/usr/bin/env python

import battle
import jsonobject
import logging
import model


logger = logging.getLogger('kcaa.kcsapi.expedition')


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
    cell_id = jsonobject.JSONProperty('cell_id', value_type=int)
    """ID of the current cell."""
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

    # Preferred formation. This will override the default formation passed to
    # GoOnExpedition.
    PREFERRED_FORMATION = {
    }

    def update(self, api_name, request, response, objects, debug):
        super(Expedition, self).update(api_name, request, response, objects,
                                       debug)
        if api_name in ('/api_req_map/start',
                        '/api_req_map/next'):
            if api_name == '/api_req_map/start':
                self.fleet_id = int(request.api_deck_id)
                self.maparea_id = int(request.api_maparea_id)
                self.map_id = int(request.api_mapinfo_no)
                self.cell_boss = response.api_data.api_bosscell_no
            self.needs_compass = response.api_data.api_rashin_flg == 1
            # api_rashin_id might represent the animation pattern of the
            # compass. Not useful here anyways.
            self.cell_id = response.api_data.api_no
            self.cell_next = response.api_data.api_next
            self.is_terminal = response.api_data.api_next == 0
            self.event = response.api_data.api_event_id
            # Other potentially interesting data:
            # - api_color_no: probably identical to api_event_id
            # - api_event_kind: additional info on the event?
            # - api_production_kind: probably the category of the found item
            # - api_enemy: enemy info (useful if submarines)
            logger.debug('rashin_flg (id): {} ({})'.format(
                response.api_data.api_rashin_flg,
                response.api_data.api_rashin_id))
            logger.debug('event_id (color_no): {} ({})'.format(
                response.api_data.api_event_id,
                response.api_data.api_color_no))
            logger.debug('production_kind: {}'.format(
                response.api_data.api_production_kind))
            logger.debug('comment_kind: {}'.format(
                response.api_data.api_comment_kind))
            logger.debug('enemy : {}'.format(str(response.api_data.api_enemy)))

    def get_preferred_formation(self, default_formation):
        return Expedition.PREFERRED_FORMATION.get(
            (self.maparea_id, self.map_id), default_formation)


class ExpeditionResult(model.KCAAObject):
    """Result of the latest expedition battle."""

    result = jsonobject.JSONProperty('result', value_type=int)
    """Resuslt of the battle."""
    got_ship = jsonobject.JSONProperty('got_ship', value_type=bool)
    """Whether got a ship as a reward."""
    new_ship_id = jsonobject.JSONProperty('new_ship_id', value_type=int)
    """Ship definition ID of the new ship."""

    def update(self, api_name, request, response, objects, debug):
        super(ExpeditionResult, self).update(api_name, request, response,
                                             objects, debug)
        if api_name in ('/api_req_sortie/battleresult',
                        '/api_req_combined_battle/battleresult'):
            self.result = battle.Battle.get_result_for_win_rank(
                response.api_data.api_win_rank)
            self.got_ship = response.api_data.api_get_flag[1] == 1
            if self.got_ship:
                self.new_ship_id = response.api_data.api_get_ship.api_ship_id
            else:
                self.new_ship_id = None
