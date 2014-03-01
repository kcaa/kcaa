#!/usr/bin/env python

from kcaa import task


class Screen(object):

    def __init__(self, manager):
        self.manager = manager

    def add_task(self, t):
        self.manager.add_task(t)

    def click(self, x, y):
        self.manager.click(x, y)

    def change_screen(self, screen_id):
        def do_task(task):
            self.click(40, 40)
            print('Changed screen to {}'.format(screen_id))
            yield 2.0
            self.click(40, 40)
            print('Changed screen to {}??'.format(screen_id))
        return self.manager.add_task(do_task)


class Manipulator(task.Task):

    def __init__(self, manager, **kwargs):
        # Be sure to store required fields before calling super(), because
        # super() will call run() inside it.
        self.objects = manager.objects
        self._screen_manager = manager.screen_manager
        super(Manipulator, self).__init__(**kwargs)

    @property
    def screen(self):
        return self._screen_manager.current_screen
