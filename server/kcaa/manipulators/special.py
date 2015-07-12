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


class AutoTimeKiller(base.AutoManipulator):

    # Parameters for the gamma distribution that decides the wait interval.
    interval_alpha = 5.0
    interval_beta = 240.0
    max_interval_sec = 3600.0
    # Parameters for the gamma distribution that decides the wait duration.
    duration_alpha = 2.0
    duration_beta = 180.0
    # Maximum seconds to wait.
    max_wait_sec = 1200.0

    next_wait = None

    @classmethod
    def precondition(cls, owner):
        return not cls.next_wait or datetime.datetime.now() > cls.next_wait

    @classmethod
    def can_trigger(cls, owner):
        to_wait = cls.next_wait is not None
        interval_sec = random.gammavariate(AutoTimeKiller.interval_alpha,
                                           AutoTimeKiller.interval_beta)
        interval_sec = min(interval_sec, AutoTimeKiller.max_interval_sec)
        cls.next_wait = (datetime.datetime.now() +
                         datetime.timedelta(seconds=interval_sec))
        logger.info('Next AutoTimeKiller trigger: {}'.format(cls.next_wait))
        if to_wait:
            return {}

    def run(self):
        wait_sec = random.gammavariate(AutoTimeKiller.duration_alpha,
                                       AutoTimeKiller.duration_beta)
        wait_sec = min(wait_sec, AutoTimeKiller.max_wait_sec)
        wait_time = datetime.timedelta(seconds=wait_sec)
        logger.info('Killing time for {}.'.format(wait_time))
        next_update = datetime.datetime.now() + wait_time
        logger.info('Scheduled next wake up: {}'.format(next_update))
        yield wait_sec


class AutoIdleTimeKiller(base.AutoManipulator):

    # Parameters to the gamma distribution that decides the wait duration.
    # Mean: alpha * beta
    # Variance = alpha * beta^2
    alpha = 3.0
    beta = 60.0
    # Maximum seconds to wait.
    max_wait_sec = 600.0

    to_wait = False

    @classmethod
    def run_only_when_idle(cls):
        return True

    @classmethod
    def can_trigger(cls, owner):
        if cls.to_wait:
            return {}
        cls.to_wait = True

    def run(self):
        wait_sec = random.gammavariate(AutoIdleTimeKiller.alpha,
                                       AutoIdleTimeKiller.beta)
        wait_sec = min(wait_sec, AutoIdleTimeKiller.max_wait_sec)
        wait_time = datetime.timedelta(seconds=wait_sec)
        logger.info('Killing time for {}.'.format(wait_time))
        next_update = datetime.datetime.now() + wait_time
        logger.info('Scheduled next wake up: {}'.format(next_update))
        yield wait_sec
