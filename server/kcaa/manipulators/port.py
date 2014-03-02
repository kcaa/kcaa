#!/usr/bin/env python

import base
from kcaa import screens


class Charge(base.Manipulator):
    def run(self, fleet_id):
        yield self.screen.change_screen(screens.PORT_LOGISTICS)
