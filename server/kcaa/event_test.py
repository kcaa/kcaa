#!/usr/bin/env python

import pytest

import event


class TestEvent(object):

    class Counter(object):

        fire_count = 0
        popped_earg = None

        def on_fired(self, sender, earg=None):
            self.fire_count += 1
            if earg is not None:
                self.popped_earg = earg.pop()

        def on_fired_sender(self, sender, earg=None):
            self.fire_count += 1
            assert sender == earg

        def on_fired_args(self, sender, foo, bar, baz):
            self.fire_count += 1
            assert foo == 'foo'
            assert bar == 'bar'
            assert baz == 'baz'

    def pytest_funcarg__one(self, request):
        class ObjectOne(object):
            event1 = event.Event()

        return ObjectOne()

    def pytest_funcarg__two(self, request):
        class ObjectTwo(object):
            event1 = event.Event()
            event2 = event.Event()

        return ObjectTwo()

    def pytest_funcarg__onep(self, request):
        class ObjectOneProperty(object):
            _event1 = event.Event()

            @property
            def event1(self):
                return self._event1

            @event1.setter
            def event1(self, value):
                pass

        return ObjectOneProperty()

    def test_one_classic(self, one):
        counter1 = TestEvent.Counter()
        one.event1.add(counter1.on_fired)
        assert counter1.fire_count == 0
        one.event1.fire()
        assert counter1.fire_count == 1
        one.event1.fire(['hello'])
        assert counter1.fire_count == 2
        assert counter1.popped_earg == 'hello'
        one.event1.remove(counter1.on_fired)
        one.event1.fire()
        assert counter1.fire_count == 2

    def test_one(self, one):
        counter1 = TestEvent.Counter()
        one.event1 += counter1.on_fired
        assert counter1.fire_count == 0
        one.event1()
        assert counter1.fire_count == 1
        one.event1(['hello'])
        assert counter1.fire_count == 2
        assert counter1.popped_earg == 'hello'
        one.event1 -= counter1.on_fired
        one.event1()
        assert counter1.fire_count == 2

    def test_one_sender(self, one):
        counter1 = TestEvent.Counter()
        one.event1 += counter1.on_fired_sender
        one.event1(one)
        assert counter1.fire_count == 1

    def test_one_args(self, one):
        counter1 = TestEvent.Counter()
        one.event1 += counter1.on_fired_args
        one.event1('foo', baz='baz', bar='bar')
        assert counter1.fire_count == 1

    def test_one_multi(self, one):
        counter1 = TestEvent.Counter()
        counter2 = TestEvent.Counter()
        one.event1 += counter1.on_fired
        one.event1 += counter2.on_fired
        assert counter1.fire_count == 0
        assert counter2.fire_count == 0
        one.event1()
        assert counter1.fire_count == 1
        assert counter2.fire_count == 1
        one.event1(['hello', 'world'])
        assert counter1.fire_count == 2
        assert counter2.fire_count == 2
        assert counter1.popped_earg == 'world'
        assert counter2.popped_earg == 'hello'
        one.event1 -= counter1.on_fired
        one.event1()
        assert counter1.fire_count == 2
        assert counter2.fire_count == 3
        one.event1 -= counter1.on_fired  # this is done twice intentionally
        one.event1 -= counter2.on_fired
        one.event1()
        assert counter1.fire_count == 2
        assert counter2.fire_count == 3

    def test_one_multi_add_remove(self, one):
        counter1 = TestEvent.Counter()
        counter2 = TestEvent.Counter()
        one.event1 += counter1.on_fired
        one.event1 += counter2.on_fired
        assert counter1.fire_count == 0
        assert counter2.fire_count == 0
        one.event1 -= counter1.on_fired
        one.event1 += counter2.on_fired
        one.event1()
        assert counter1.fire_count == 0
        assert counter2.fire_count == 2
        one.event1 -= counter2.on_fired
        one.event1()
        assert counter1.fire_count == 0
        assert counter2.fire_count == 2

    def test_one_multi_run_once(self, one):
        counter1 = TestEvent.Counter()
        counter2 = TestEvent.Counter()
        counter3 = TestEvent.Counter()
        one.event1 += counter1.on_fired
        one.event1 <<= counter2.on_fired
        one.event1.add(event.RunOnceEventHandler(counter3.on_fired))
        assert counter1.fire_count == 0
        assert counter2.fire_count == 0
        assert counter3.fire_count == 0
        one.event1()
        assert counter1.fire_count == 1
        assert counter2.fire_count == 1
        assert counter3.fire_count == 1
        one.event1(['hello'])
        assert counter1.fire_count == 2
        assert counter2.fire_count == 1
        assert counter3.fire_count == 1
        assert counter1.popped_earg == 'hello'

    def test_two(self, two):
        counter1 = TestEvent.Counter()
        counter2 = TestEvent.Counter()
        two.event1 += counter1.on_fired
        two.event2 += counter2.on_fired
        assert counter1.fire_count == 0
        assert counter2.fire_count == 0
        two.event1()
        assert counter1.fire_count == 1
        assert counter2.fire_count == 0
        two.event2()
        assert counter1.fire_count == 1
        assert counter2.fire_count == 1
        two.event2()
        assert counter1.fire_count == 1
        assert counter2.fire_count == 2
        two.event1()
        assert counter1.fire_count == 2
        assert counter2.fire_count == 2
        two.event1 -= counter1.on_fired
        two.event1()
        assert counter1.fire_count == 2
        assert counter2.fire_count == 2
        two.event2 -= counter2.on_fired
        two.event2()
        assert counter1.fire_count == 2
        assert counter2.fire_count == 2

    def test_onep(self, onep):
        counter1 = TestEvent.Counter()
        onep.event1 += counter1.on_fired
        assert counter1.fire_count == 0
        onep.event1.fire()
        assert counter1.fire_count == 1
        onep.event1.remove(counter1.on_fired)
        onep.event1.fire()
        assert counter1.fire_count == 1
        onep.event1 += counter1.on_fired
        assert counter1.fire_count == 1
        onep.event1()
        assert counter1.fire_count == 2
        onep.event1 -= counter1.on_fired
        onep.event1()
        assert counter1.fire_count == 2


class TestEventHandler(object):

    def test_call_function(self):
        def function(sender, earg):
            assert sender == 'sender'
            earg.append('earg')

        handler = event.EventHandler(function)
        earg = []
        assert handler('sender', earg) == handler
        assert earg == ['earg']

    def test_call_method(self):
        class Class(object):
            def method(self, sender, earg):
                assert sender == 'sender'
                earg.append('earg')

        handler = event.EventHandler(Class().method)
        earg = []
        assert handler('sender', earg) == handler
        assert earg == ['earg']


class TestRunOnceEventHandler(object):

    def test_call_function(self):
        def function(sender, earg):
            assert sender == 'sender'
            earg.append('earg')

        handler = event.RunOnceEventHandler(function)
        earg = []
        assert handler('sender', earg) is None
        assert earg == ['earg']

    def test_call_method(self):
        class Class(object):
            def method(self, sender, earg):
                assert sender == 'sender'
                earg.append('earg')

        handler = event.RunOnceEventHandler(Class().method)
        earg = []
        assert handler('sender', earg) is None
        assert earg == ['earg']


def main():
    import doctest
    doctest.testmod(event)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
