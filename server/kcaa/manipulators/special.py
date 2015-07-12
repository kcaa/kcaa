#!/usr/bin/env python

import datetime
import logging
import random

import base
from kcaa import screens


logger = logging.getLogger('kcaa.manipulators.special')


class AutoStartGame(base.AutoManipulator):

    @classmethod
    def can_trigger(cls, owner):
        if owner.screen_id == screens.SPECIAL_START:
            return {}

    def run(self):
        self.screen.assert_screen(screens.SPECIAL_START)
        yield self.screen.proceed()


class AutoIdleTimeKiller(base.AutoManipulator):

    # Parameters to the gamma distribution.
    # Mean: alpha * beta
    # Variance = alpha * beta^2
    alpha = 15.0
    beta = 10.0
    # Maximum seconds to wait.
    max_wait_sec = 300.0

    @classmethod
    def run_only_when_idle(cls):
        return True

    @classmethod
    def can_trigger(cls, owner):
        return {}

    def run(self):
        wait_sec = random.gammavariate(AutoIdleTimeKiller.alpha,
                                       AutoIdleTimeKiller.beta)
        wait_sec = min(wait_sec, AutoIdleTimeKiller.max_wait_sec)
        wait_time = datetime.timedelta(seconds=wait_sec)
        logger.info('Killing time for {}.'.format(wait_time))
        next_update = datetime.datetime.now() + wait_time
        logger.info('Scheduled next wake up: {}'.format(next_update))
        yield wait_sec
