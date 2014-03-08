#!/usr/bin/env python
"""
Event handling.

Basic design of Event and EventProxy is derived from the code written by:
Masaaki Shibata <mshibata@emptypage.jp> http://www.emptypage.jp/

The original code is in the public domain. The document which describes the
original code is located at:
http://www.emptypage.jp/notes/pyevent.html
"""


class Event(object):
    """
    Event.
    """

    __slots__ = ['__doc__']

    def __init__(self):
        """
        Create an event.
        """
        pass

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return EventProxy(self, obj)

    def __set__(self, obj, value):
        pass


class EventProxy(object):
    """
    Event proxy, administering event handlers and propagate events.
    """

    __slots__ = ['_event', '_sender']

    def __init__(self, event, sender):
        """
        Create an event proxy.
        """
        self._event = event
        self._sender = sender

    def _get_handlers(self):
        if hasattr(self._sender, '__eventhandler__'):
            eventhandler = self._sender.__eventhandler__
        else:
            eventhandler = self._sender.__eventhandler__ = {}
        return eventhandler.setdefault(self._event, [])

    def add(self, handler):
        """
        Add a new event handler.

        :param handler: event handler or callable object

        This method adds *handler* to the registered event handler list.
        Registered event handlers will be called in the order they were
        registered. If *handler* is not an instance of :class:`EventHandler`,
        a new :class:`EventHandler` is created with *handler*.

        If you do not have your customized event handler, it is encouraged that
        you use '+=' operator or '<<=' operator instead. See :meth:`__iadd__`
        or :meth:`__lshift__`.
        """
        if isinstance(handler, EventHandler):
            self._get_handlers().append(handler)
        else:
            self._get_handlers().append(EventHandler(handler))
        return self

    def remove(self, handler):
        """
        Remove the event handler.

        :param handler: event handler or callable object

        This method removes *handler* from the registered event handler list.
        *handler* can be either an instance of :class:`EventHandler` or a
        callable object. If more than one handler identical to *handler* is
        registered, they are all removed.

        You can remove a handler also by using '-=' operator::

            foo.clicked -= handler
        """
        handlers = self._get_handlers()
        if isinstance(handler, EventHandler):
            handlers[:] = filter(lambda h: h is not handler, handlers)
        else:
            # Note that bound method objects are not the same instances;
            # Do not use 'h.callable is not handler'
            handlers[:] = filter(lambda h: h.callable != handler, handlers)
        return self

    def fire(self, *args, **kwargs):
        """
        Fire the event and call the registered event handlers.

        :param args: positional arguments passed to event handlers
        :param kwargs: keyword arguments passed to event handlers

        This method calls all the registered event handlers. Registered event
        handlers will be called in the order they were registered.

        The value of *args* and *kwargs* will propagate to each registered
        handler.

        You can call the event itself instead of this method::

            foo.clicked(some_parameter, another_parameter)
        """
        handlers = self._get_handlers()
        handlers[:] = filter(None, (handler(self._sender, *args, **kwargs) for
                                    handler in handlers))

    def __iadd__(self, callable):
        """
        Add a new event handler.

        :param callable: callable

        This method creates an :class:`EventHandler` with *callable* and adds
        it to the registered event handler list. Registered event handlers
        will be called in the order they were registered.

        Event handlers can be either a function or a method. It has to have
        at least one parameter *sender*, so handlers will take a form of::

            def function(sender):
                # some code to handle the event....
                pass

        Or::

            class Observer(object):
                def method(self, sender):
                    # some code to handle the event....
                    pass

        The value of *sender* will be the owner; that is, the object to which
        the event belongs.

        If the description of an event says that it has some parameters, event
        handlers also should have parameters to receive arguments passed for
        raising the event. For example, if an event has two parameters *foo*
        and *bar* in this order, an event handler of it should be::

            def function(sender, foo, bar):
                # you can do some task using foo and bar....
                pass

        Or::

            class Observer(object):
                def method(self, sender, foo, bar):
                    # you can do some task using foo and bar....
                    pass

        You can add a handler also by using '+=' operator::

            foo.clicked += function
            foo.clicked += Observer().method

        If you want to add a handler which runs only once, use '<<=' operator
        instead::

            foo.clicked <<= function
            foo.clicked <<= Observer().method
        """
        return self.add(EventHandler(callable))

    def __ilshift__(self, callable):
        """
        Add a new run-once event handler.

        :param callable: callable

        This method creates a :class:`RunOnceEventHandler`, not an
        :class:`EventHandler`, with *callable* and adds it to the registered
        event handler list. For the rest part this method is the same as
        :meth:`__add__`. See :meth:`__add__` for details.

        You can add a run-once handler also by '<<=' operator::

            foo.clicked <<= function
            foo.clicked <<= Observer().method

        If you add a regular handler which is called every time until being
        removed, use '+=' operator instead::

            foo.clicked += function
            foo.clicked += Observer().method

        """
        return self.add(RunOnceEventHandler(callable))

    __isub__ = remove
    __call__ = fire


class EventHandler(object):
    """
    Event handler.

    :param callable: callable object
    """

    def __init__(self, callable):
        """
        Create an event handler.
        """
        self._callable = callable

    @property
    def callable(self):
        """
        The callable object.
        """
        return self._callable

    def __call__(self, sender, *args, **kwargs):
        """
        Call the callable.

        :param sender: sender of the event
        :param args: positional arguments passed to event handlers
        :param kwargs: keyword arguments passed to event handlers
        """
        self._callable(sender, *args, **kwargs)
        return self


class RunOnceEventHandler(EventHandler):
    """
    *Run-Once* Event handler, which is called only once.

    :param callable: callable object
    """

    def __init__(self, callable):
        """
        Create a run-once event handler.
        """
        super(RunOnceEventHandler, self).__init__(callable)

    def __call__(self, sender, *args, **kwargs):
        """
        Call the callable object.

        :param sender: sender of the event
        :param args: positional arguments passed to event handlers
        :param kwargs: keyword arguments passed to event handlers
        """
        self._callable(sender, *args, **kwargs)
        return None


if __name__ == '__main__':
    import event_test
    event_test.main()
