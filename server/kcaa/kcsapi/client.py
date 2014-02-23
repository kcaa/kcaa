#!/usr/bin/env python

import jsonobject
import model


class Screen(model.KCAAObject):
    """Current screen.

    This object provides the best guess of the current screen that the client
    (Kancolle Flash player) is currently showing to the user.
    """

    SCREEN_UNKNOWN = 0
    screen = jsonobject.JSONProperty('screen', SCREEN_UNKNOWN, value_type=int)
    """Current screen."""
    SCREEN_SPECIAL = 1
    SCREEN_SPECIAL_START = 101
    SCREEN_PORT = 2
    SCREEN_PORT_MAIN = 200
    SCREEN_PORT_RECORD = 201
    SCREEN_PORT_ENCYCLOPEDIA = 202
    SCREEN_PORT_ITEMRACK = 203
    SCREEN_PORT_FURNITURE = 204
    SCREEN_PORT_QUESTLIST = 205
    SCREEN_PORT_ITEMSHOP = 206
    SCREEN_PORT_EXPEDITION = 207
    SCREEN_PORT_PRACTICE = 208
    SCREEN_PORT_MISSION = 209
    SCREEN_PORT_ORGANIZING = 210
    SCREEN_PORT_LOGISTICS = 211
    SCREEN_PORT_REBUILDING = 212
    SCREEN_PORT_REPAIR = 213
    SCREEN_PORT_SHIPYARD = 214
    SCREEN_PRACTICE = 4
    SCREEN_PRACTICE_BATTLE = 400
    SCREEN_PRACTICE_BATTLERESULT = 401

    API_SCREEN_TO_SCREEN_MAP = {
    }
    API_TO_SCREEN_MAP = {
        '/api_get_master/mapinfo': SCREEN_PORT_EXPEDITION,
        '/api_get_master/mission': SCREEN_PORT_MISSION,
        '/api_get_master/payitem': SCREEN_PORT_ITEMSHOP,
        '/api_get_member/book2': SCREEN_PORT_ENCYCLOPEDIA,
        '/api_get_member/deck_port': SCREEN_PORT_MAIN,
        '/api_get_member/practice': SCREEN_PORT_PRACTICE,
        '/api_get_member/questlist': SCREEN_PORT_QUESTLIST,
        '/api_req_practice/battle': SCREEN_PRACTICE_BATTLE,
        '/api_req_practice/battle_result': SCREEN_PRACTICE_BATTLERESULT,
        '/api_start': SCREEN_SPECIAL_START,
    }

    def update(self, api_name, response, objects):
        super(Screen, self).update(api_name, response, objects)
        # Use the previous screen and API name to guess the current screen.
        if api_name in Screen.API_SCREEN_TO_SCREEN_MAP:
            for transition_rule in Screen.API_SCREEN_TO_SCREEN_MAP[api_name]:
                if Screen.in_category(self.screen, transition_rule[0]):
                    self.screen = transition_rule[1]
                    break
        # Some API names are unique enough to identify the current screen.
        elif api_name in Screen.API_TO_SCREEN_MAP:
            self.screen = Screen.API_TO_SCREEN_MAP[api_name]

    @staticmethod
    def in_category(screen, category):
        while screen > category:
            screen /= 100
        return screen == category
