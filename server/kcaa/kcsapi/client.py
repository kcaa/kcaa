#!/usr/bin/env python

import jsonobject
from kcaa import screens
import model


class Screen(model.KCAAObject):
    """Current screen.

    This object provides the best guess of the current screen that the client
    (Kancolle Flash player) is currently showing to the user.
    """

    screen = jsonobject.JSONProperty('screen', screens.UNKNOWN, value_type=int)
    """Current screen."""

    API_SCREEN_TO_SCREEN_MAP = {
    }
    API_TO_SCREEN_MAP = {
        '/api_get_master/mapinfo': screens.PORT_EXPEDITION,
        '/api_get_master/mission': screens.PORT_MISSION,
        '/api_get_master/payitem': screens.PORT_ITEMSHOP,
        '/api_get_member/book2': screens.PORT_ENCYCLOPEDIA,
        '/api_get_member/deck_port': screens.PORT_MAIN,
        '/api_get_member/practice': screens.PORT_PRACTICE,
        '/api_get_member/questlist': screens.PORT_QUESTLIST,
        '/api_req_practice/battle': screens.PRACTICE_BATTLE,
        '/api_req_practice/battle_result': screens.PRACTICE_BATTLERESULT,
        '/api_start': screens.SPECIAL_START,
    }

    def update(self, api_name, request, response, objects, debug):
        super(Screen, self).update(api_name, request, response, objects, debug)
        # Use the previous screen and API name to guess the current screen.
        if api_name in Screen.API_SCREEN_TO_SCREEN_MAP:
            for transition_rule in Screen.API_SCREEN_TO_SCREEN_MAP[api_name]:
                if screens.in_category(self.screen, transition_rule[0]):
                    self.screen = transition_rule[1]
                    break
        # Some API names are unique enough to identify the current screen.
        elif api_name in Screen.API_TO_SCREEN_MAP:
            self.screen = Screen.API_TO_SCREEN_MAP[api_name]
