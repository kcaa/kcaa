#!/usr/bin/env python

from kcaa import task


class Screen(object):

    def __init__(self, manager):
        self.manager = manager

    def do_task(self, t, *args, **kwargs):
        return self.manager.add_task(t, *args, **kwargs)

    def click(self, x, y):
        self.manager.click(x, y)

    @property
    def screen_id(self):
        return self.manager.objects['Screen'].screen

    def update_screen_id(self, screen_id):
        """Update screen ID explicitly.

        This method explicitly updates the screen ID maintained by
        :class:`kcaa.kcsapi.client.Screen`. This is not required if the screen
        transition can be detected by it (like port to quest list screen), but
        necessary if the client doesn't sent any requests.
        """
        self.manager.objects['Screen'].screen = screen_id
        self.manager.updated_object_types.add('Screen')

    def wait_screen_transition(self, screen_id, buffer_delay=2.0):
        def wait_screen_transition_task(task):
            while self.screen_id != screen_id:
                print 'Waiting for transition to {} (current: {})'.format(
                    screen_id, self.screen_id)
                yield 2.0
            print 'Transitioned! Waiting for the buffer.'
            yield buffer_delay
        return self.do_task(wait_screen_transition_task)

    def change_screen(self, screen_id):
        def change_screen_task(task):
            self.click(560, 50)
            print('Quest list button clicked')
            yield self.wait_screen_transition(screen_id)
        return self.do_task(change_screen_task)


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
