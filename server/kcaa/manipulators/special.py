#!/usr/bin/env python

import base
from kcaa import screens


class StartGame(base.Manipulator):
    def run(self):
        self.screen.assert_screen(screens.SPECIAL_START)
        yield self.screen.proceed()
