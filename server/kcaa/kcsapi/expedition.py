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
    cell_boss = jsonobject.JSONProperty('cell_boss', value_type=int)
    """ID of the cell where a boss lives."""
    cell_id = jsonobject.JSONProperty('cell_id', value_type=int)
    """ID of the cell on the next move.

    Cell ID is assigned from 0 (the start cell).
    Note that this is deterministically available when a compass is presented.
    """
    is_terminal = jsonobject.JSONProperty('is_terminal', value_type=bool)
    """Whether the next cell is the terminal of the path."""
    needs_compass = jsonobject.JSONProperty('needs_compass', value_type=bool)
    """Whether needs a compass on the next move."""
    needs_active_selection = jsonobject.JSONProperty('needs_active_selection',
                                                     value_type=bool)
    """Whether needs an active selection from the player on the next move."""
    next_cell_selections = jsonobject.JSONProperty(
        'next_cell_selections', value_type=list, element_type=int)
    """Next cells selectable for the active selection."""
    event = jsonobject.JSONProperty('event', value_type=int)
    """Event that will happen in the cell."""
    EVENT_ITEM = 2
    EVENT_BATTLE = 4
    EVENT_BATTLE_BOSS = 5
    EVENT_ACTIVE_SELECTION = 6
    produced_item = jsonobject.JSONProperty('produced_item', value_type=int)
    """Item produced in the next cell."""
    PRODUCTION_NONE = 0

    @property
    def location_id(self):
        return (self.maparea_id, self.map_id, self.cell_id)

    def update(self, api_name, request, response, objects, debug):
        super(Expedition, self).update(api_name, request, response, objects,
                                       debug)
        if api_name in ('/api_req_map/start',
                        '/api_req_map/next'):
            data = response.api_data
            if api_name == '/api_req_map/start':
                self.fleet_id = int(request.api_deck_id)
                self.maparea_id = int(request.api_maparea_id)
                self.map_id = int(request.api_mapinfo_no)
                self.cell_boss = data.api_bosscell_no
                self.produced_item = Expedition.PRODUCTION_NONE
            else:
                self.produced_item = data.api_production_kind
            # api_rashin_id might represent the animation pattern of the
            # compass. Not useful here anyways.
            self.cell_id = data.api_no
            self.is_terminal = data.api_next == 0
            self.needs_compass = data.api_rashin_flg == 1
            self.event = data.api_event_id
            if self.event == Expedition.EVENT_ACTIVE_SELECTION:
                self.needs_active_selection = True
                self.next_cell_selections = (
                    data.api_select_route.api_select_cells)
            else:
                self.needs_active_selection = False
                self.next_cell_selections = None

            logger.debug('Current: {}-{}-{}'.format(
                self.maparea_id, self.map_id, self.cell_id))
            logger.debug('Boss:    {}-{}-{}'.format(
                self.maparea_id, self.map_id, self.cell_boss))
            logger.debug('Event: {} (kind: {}, color: {})'.format(
                self.event, data.api_event_kind, data.api_color_no))
            logger.debug('Item produced: {}'.format(self.produced_item))
            logger.debug('Needs compass: {}'.format(self.needs_compass))
            logger.debug('Needs active selection: {}'.format(
                self.needs_active_selection))
            if self.needs_active_selection:
                logger.debug('  Selections: {}'.format(
                    self.next_cell_selections))
            # Other potentially interesting data:
            # - api_color_no: probably the color of the next cell after the
            #                 exact event is revealed
            # - api_event_kind: additional info on the event?
            # - api_production_kind: probably the category of the found item
            # - api_enemy: enemy info (useful if submarines)
            logger.debug('cell_next: {}'.format(data.api_cell_next))
            logger.debug('rashin_flg (id): {} ({})'.format(
                data.api_rashin_flg, data.api_rashin_id))
            if hasattr(data, 'api_enemy'):
                logger.debug('enemy : {}'.format(str(data.api_enemy)))


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
