#!/usr/bin/env python

from kcaa import task


class Screen(object):

    def __init__(self, manager):
        self.manager = manager

    def add_task(self, t):
        self.manager.add_task(t)

    def click(self, x, y):
        self.manager.click(x, y)

    def update_screen_id(self, screen_id):
        """Update screen ID explicitly.

        This method explicitly updates the screen ID maintained by
        :class:`kcaa.kcsapi.client.Screen`. This is not required if the screen
        transition can be detected by it (like port to quest list screen), but
        necessary if the client doesn't sent any requests.
        """
        self.manager.objects['Screen'].screen = screen_id
        self.manager.updated_object_types.add('Screen')

    def change_screen(self, screen_id):
        def do_task(task):
            self.click(40, 40)
            print('Changed screen to {}'.format(screen_id))
            yield 2.0
            self.click(40, 40)
            self.update_screen_id(screen_id)
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
