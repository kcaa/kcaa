#!/usr/bin/env python

import base
from kcaa import screens


class AutoStartGame(base.AutoManipulator):

    @classmethod
    def can_trigger(cls, owner):
        if owner.screen_id == screens.SPECIAL_START:
            return {}

    def run(self):
        self.screen.assert_screen(screens.SPECIAL_START)
        yield self.screen.proceed()
