#!/usr/bin/env python

import jsonobject
import model


class Screen(model.KCAAObject):
    """Current screen.

    This object provides the best guess of the current screen that the client
    (Kancolle Flash player) is currently showing to the user.
    """

    screen = jsonobject.JSONProperty('screen', value_type=int)
    """Current screen."""
    SCREEN_START = 1
    SCREEN_PORT = 100

    API_TO_SCREEN_MAP = {
        '/api_start': SCREEN_START,
        '/api_get_member/deck_port': SCREEN_PORT,
    }

    def update(self, api_name, response):
        super(Screen, self).update(api_name, response)
        if api_name in Screen.API_TO_SCREEN_MAP:
            self.screen = Screen.API_TO_SCREEN_MAP[api_name]
