#!/usr/bin/env python

import base


class Charge(base.Manipulator):
    def run(self, fleet_id):
        print('Charge: {}'.format(fleet_id))
        yield self.screen.change_screen(201)
        print('Charge finished')
