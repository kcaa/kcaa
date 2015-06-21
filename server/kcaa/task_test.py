#!/usr/bin/env python

import pytest

import task


def run_manager(manager, duration, step=0.01):
    start = manager.time
    end = start + duration
    current = start
    while current <= end:
        manager.update(current)
        current += step


class TestTask(object):

    def test_init(self):
        class Task(task.Task):
            done = False

            def run(self, a, b, c, *args, **kwargs):
                assert a == 123
                assert b == 456.789
                assert c is None
                assert args == ('foo', 'bar', 'baz')
                assert kwargs == {'apple': 12, 'orange': 34}
                self.done = True
                yield self.unit

        t = Task(123, 456.789, None, 'foo', 'bar', 'baz', apple=12, orange=34)
        assert not t.done
        t.update(0.0)
        assert t.done

    def test_taskinfo(self):
        class Task(task.Task):
            finalized = False

            def run(self):
                assert self.count == 1
                assert self.time < 0.1
                yield 0.1
                assert self.count == 2
                assert self.time >= 0.1 and self.time < 0.11
                last = self.time
                yield 0.1
                assert self.count == 3
                assert self.time >= 0.2 and self.time < 0.21
                assert (self.time - last) - self.dtime < 1.0e-5

            def finalize(self):
                self.finalized = True

        manager = task.TaskManager(12345.0)
        t = Task()
        manager.add(t)
        run_manager(manager, 0.5)
        assert t.finalized

    def test_update(self):
        class Task(task.Task):
            called = 0

            def run(self):
                self.called += 1
                yield 0.1
                self.called += 1
                yield 0.1
                self.called += 1

        t = Task()
        assert t.called == 0
        t.update(0.0)
        assert t.called == 1
        t.update(0.05)
        assert t.called == 1
        t.update(0.09)
        assert t.called == 1
        t.update(0.1)
        assert t.called == 2
        t.update(0.11)
        assert t.called == 2
        t.update(0.19)
        assert t.called == 2
        with pytest.raises(StopIteration):
            t.update(0.2)
        assert t.called == 3
        with pytest.raises(StopIteration):
            t.update(10.0)
        assert t.called == 3

    def test_update_epoch(self):
        class Task(task.Task):
            called = 0

            def run(self):
                self.called += 1
                yield 0.1
                self.called += 1
                yield 0.1
                self.called += 1

        manager = task.TaskManager(12345.0)
        t = Task()
        manager.add(t)
        assert t.called == 0
        manager.update(12345.0)
        assert t.called == 1
        manager.update(12345.05)
        assert t.called == 1
        manager.update(12345.09)
        assert t.called == 1
        manager.update(12345.11)
        assert t.called == 2
        manager.update(12345.19)
        assert t.called == 2
        manager.update(12345.21)
        assert t.called == 3
        manager.update(12346.0)
        assert t.called == 3

    def test_update_smalldelay(self):
        class Task(task.Task):
            called = 0

            def run(self):
                self.called += 1
                yield 0.0
                self.called += 1
                yield 0.1
                self.called += 1
                yield 0.1
                self.called += 1

        t = Task()
        assert t.called == 0
        t.update(0.0)
        assert t.called == 2
        with pytest.raises(StopIteration):
            t.update(0.2)
        assert t.called == 4

    def test_update_unit(self):
        class Task(task.Task):
            def run(self):
                assert self.time >= 0.0 and self.time < 0.01
                yield self.unit
                assert self.time >= 0.1 and self.time < 0.11
                yield self.unit
                assert self.time >= 0.2 and self.time < 0.21
                yield self.unit
                assert self.time >= 0.3 and self.time < 0.31
                yield 1.0
                assert self.time >= 1.3 and self.time < 1.31

        t = Task()
        t.update(0.0)
        t.update(0.1)
        t.update(0.2)
        t.update(0.3)
        t.update(0.4)
        t.update(0.5)
        t.update(0.6)
        t.update(0.7)
        t.update(0.8)
        t.update(0.9)
        t.update(1.0)
        t.update(1.1)
        t.update(1.2)
        with pytest.raises(StopIteration):
            t.update(1.3)

    def test_update_unit_interleaved(self):
        class Task(task.Task):
            def run(self):
                assert self.time >= 0.00 and self.time < 0.10
                yield 0.05
                assert self.time >= 0.05 and self.time < 0.15
                yield self.unit
                assert self.time >= 0.15 and self.time < 0.25
                yield 0.05
                assert self.time >= 0.20 and self.time < 0.30
                yield self.unit
                assert self.time >= 0.30 and self.time < 0.40

        t = Task()
        t.update(0.0)
        t.update(0.1)
        t.update(0.2)
        with pytest.raises(StopIteration):
            t.update(0.3)

    def test_update_unit_delayed_suspended(self):
        class Task(task.Task):
            def run(self):
                yield self.unit
                yield self.unit
                yield self.unit

        t = Task()
        assert t.count == 0
        t.update(0.0)
        assert t.count == 1
        t.update(1.0)
        assert t.count == 2
        t.suspend()
        t.update(100.0)
        assert t.count == 2
        t.resume()
        t.update(101.0)
        assert t.count == 3
        with pytest.raises(StopIteration):
            t.update(102.0)
        assert t.count == 4

    def test_finalize(self):
        class Task(task.Task):
            finalized = False

            def run(self, a, b, c):
                assert a == 123
                assert b == 456.789
                assert c is None
                yield 0.1

            def finalize(self, a, b, c):
                assert a == 123
                assert b == 456.789
                assert c is None
                self.finalized = True

        t = Task(123, 456.789, None)
        l = [False]

        def on_finished(sender):
            assert t.finalized
            l[0] = True

        t.finished += on_finished
        assert t.alive
        assert not t.finalized
        assert not l[0]
        t.update(0.0)
        assert t.alive
        assert not t.finalized
        assert not l[0]
        t.update(0.05)
        assert t.alive
        assert not t.finalized
        assert not l[0]
        with pytest.raises(StopIteration):
            t.update(0.1)
        assert not t.alive
        assert t.finalized
        assert l[0]
        count = t.count
        with pytest.raises(StopIteration):
            t.update(0.2)
        assert t.count == count

    def test_finalize_removed(self):
        class Task(task.Task):
            finalized = False

            def run(self, a, b, c):
                assert a == 123
                assert b == 456.789
                assert c is None
                yield 0.1

            def finalize(self, a, b, c):
                assert a == 123
                assert b == 456.789
                assert c is None
                self.finalized = True

        manager = task.TaskManager(0.0)
        t = Task(123, 456.789, None)
        manager.add(t)
        assert not t.finalized
        manager.update(0.0)
        assert not t.finalized
        manager.remove(t)
        assert t.finalized

    def test_success(self):
        class Task(task.Task):
            def run(self):
                yield 0.0

        t = Task()
        assert t.alive
        assert not t.success
        with pytest.raises(StopIteration):
            t.update(0.1)
        assert not t.alive
        assert t.success

    def test_exception(self):
        class Task(task.Task):
            finalized = False

            def run(self):
                yield 0.0
                self.thrown = Exception()
                raise self.thrown

            def finalize(self):
                self.finalized = True

        t = Task()
        assert t.alive
        assert not t.success
        with pytest.raises(Exception) as excinfo:
            t.update(0.1)
        assert excinfo.value is t.thrown
        assert not t.alive
        assert not t.success
        assert t.exception is t.thrown
        assert t.finalized

    def test_suspend_resume(self):
        class Task(task.Task):
            def run(self):
                yield 1.0

        t = Task()
        assert t.running
        t.update(0.0)
        assert t.running
        t.update(0.5)
        assert t.running
        t.suspend()
        assert not t.running
        t.update(1.5)
        assert not t.running
        t.resume()
        assert t.running
        t.update(1.99)
        with pytest.raises(StopIteration):
            t.update(2.01)
        assert not t.running
        assert t.finished

    def test_suspend_resume_epoch(self):
        class Task(task.Task):
            def run(self):
                yield 1.0

        manager = task.TaskManager(12345.0)
        t = Task()
        manager.add(t)
        assert t.running
        manager.update(12345.0)
        assert t.running
        manager.update(12345.5)
        assert t.running
        t.suspend()
        assert not t.running
        manager.update(12346.5)
        assert not t.running
        t.resume()
        assert t.running
        manager.update(12346.99)
        assert t.running
        manager.update(12347.01)
        assert not t.running
        assert t.finished

    def test_custom_return_value(self):
        class Task(task.Task):
            def run(self):
                yield 0.1
                self.custom_value = 123

        t = Task()
        assert not(hasattr(t, 'custom_value'))
        with pytest.raises(StopIteration):
            t.update(0.2)
        assert t.custom_value == 123

    def test_last_blocking(self):
        class BlockingTask(task.Task):
            def run(self):
                yield 0.1

        class Task(task.Task):
            def run(self, manager, blocking_task):
                yield manager.add(blocking_task)
                assert self.last_blocking is blocking_task

        manager = task.TaskManager(0.0)
        b = BlockingTask()
        assert b.alive
        t = Task(manager, b)
        manager.add(t)
        # Call manager.update() twice as a single call would not start running
        # the blocking task.
        # TODO: Consider running a blocking task immediately if the manager is
        # the same.
        manager.update(0.1)
        manager.update(0.2)
        assert not b.alive
        assert b.success
        assert t.last_blocking is b


class TestFunctionTask(object):

    def test_init(self):
        def do_task(task, a, b, c, *args, **kwargs):
            assert a == 123
            assert b == 456.789
            assert c == []
            assert args == ('foo', 'bar', 'baz')
            assert kwargs == {'apple': 12, 'orange': 34}
            c.append('Done')
            yield task.unit

        manager = task.TaskManager(0.0)
        c = []
        manager.add(do_task, 123, 456.789, c, 'foo', 'bar', 'baz', apple=12,
                    orange=34)
        manager.update(0.0)
        assert c == ['Done']

    def test_init_method(self):
        class ClassA(object):
            done = False

            def do_task(self, task):
                self.done = True
                yield task.unit

        class ClassB:
            done = False

            def do_task(self, task):
                self.done = True
                yield task.unit

        manager = task.TaskManager(0.0)
        a, b = ClassA(), ClassB()
        manager.add(a.do_task)
        manager.add(b.do_task)
        assert not a.done
        assert not b.done
        manager.update(0.0)
        assert a.done
        assert b.done

    def test_taskinfo(self):
        def do_task(task):
            assert task.count == 1
            assert task.time < 0.1
            yield 0.1
            assert task.count == 2
            assert task.time >= 0.1 and task.time < 0.11
            last = task.time
            yield 0.1
            assert task.count == 3
            assert task.time >= 0.2 and task.time < 0.21
            assert (task.time - last) - task.dtime < 1.0e-5

        manager = task.TaskManager(12345.0)
        manager.add(do_task)
        run_manager(manager, 0.5)

    def test_add_return_value(self):
        def do_task(task, l):
            l[0] += 1
            yield 0.1
            l[0] += 1
            yield 0.1
            l[0] += 1

        manager = task.TaskManager(0.0)
        l = [0]
        t = manager.add(do_task, l)
        assert l[0] == 0
        manager.update(0.0)
        assert l[0] == 1
        manager.update(0.1)
        assert l[0] == 2
        manager.remove(t)
        manager.update(0.2)
        assert l[0] == 2

    def test_custom_return_value(self):
        def do_task(task):
            yield 0.1
            task.custom_value = 123

        manager = task.TaskManager(0.0)
        t = manager.add(do_task)
        assert not(hasattr(t, 'custom_value'))
        manager.update(0.2)
        assert t.custom_value == 123


class TestTaskManager(object):

    def test_add_remove(self):
        class Task(task.Task):
            called = 0

            def run(self):
                self.called += 1
                yield 0.1
                self.called += 1

        t1 = Task()
        t2 = Task()
        manager = task.TaskManager(0.0)
        t1_added = manager.add(t1)
        t2_added = manager.add(t2)
        assert t1_added is t1
        assert t2_added is t2
        assert t1.called == 0
        assert t2.called == 0
        manager.update(0.0)
        assert t1.called == 1
        assert t2.called == 1
        manager.add(t1)  # this must do nothing
        manager.remove(t2)
        manager.update(0.1)
        assert t1.called == 2
        assert t2.called == 1
        manager.remove(t2)  # this must do nothing

    def test_pending_task(self):
        def child(task):
            yield 1.0

        def parent(task, manager, param):
            yield 1.0
            t = manager.add(child)
            param['child'] = t
            yield 1.0

        manager = task.TaskManager(0.0)
        param = {'child': None}
        t1 = manager.add(parent, manager, param)
        assert t1.count == 0
        manager.update(0.0)
        assert t1.count == 1
        manager.update(1.0)
        assert t1.count == 2
        t2 = param['child']
        assert t2 is not None
        assert t2.count == 1

    def test_blocking_task(self):
        def blocking(task):
            yield 3.0

        def blocked(task, manager, param):
            yield 1.0
            param['stage'] = 1
            t = manager.add(blocking)
            param['blocking'] = t
            yield t
            param['stage'] = 2
            yield 1.0

        manager = task.TaskManager(0.0)
        param = {'stage': 0, 'blocking': None}
        t1 = manager.add(blocked, manager, param)
        manager.update(0.0)
        assert t1.running
        assert param['stage'] == 0
        manager.update(0.99)
        assert t1.running
        assert param['stage'] == 0
        assert param['blocking'] is None
        manager.update(1.01)
        assert not t1.running
        assert param['stage'] == 1
        t2 = param['blocking']
        assert t2 is not None
        assert t2.running
        assert t2.count == 1
        manager.update(3.99)
        assert not t1.running
        assert t2.running
        assert param['stage'] == 1
        manager.update(4.01)
        assert t1.running
        assert not t2.running
        assert not t2.alive
        assert param['stage'] == 2
        manager.update(4.99)
        assert t1.running
        assert t1.alive
        assert param['stage'] == 2
        manager.update(5.01)
        assert not t1.running
        assert not t1.alive

    def test_exception(self):
        def throws_exception(task):
            yield 0.0
            raise Exception()

        manager = task.TaskManager(0.0)
        t = manager.add(throws_exception)
        # The TaskManager should not die, even if the task has thrown an
        # exception.
        manager.update(0.1)
        assert not t.alive
        assert not t.success
        assert t.exception

    def test_propagate_exception(self):
        def throws_exception(task):
            yield 0.0
            raise Exception()

        def receives_exception(task, manager):
            yield manager.add(throws_exception)

        manager = task.TaskManager(0.0)
        t = manager.add(receives_exception, manager)
        manager.update(0.1)
        assert not t.alive
        assert not t.success
        assert t.exception
        assert not t.last_blocking.alive
        assert not t.last_blocking.success
        assert t.last_blocking.exception is t.exception

    def test_catch_propagated_exception(self):
        def throws_exception(task):
            yield 0.0
            raise Exception()

        def receives_exception(task, manager):
            task.result = 0
            try:
                yield manager.add(throws_exception)
            except Exception:
                task.result = 123

        manager = task.TaskManager(0.0)
        t = manager.add(receives_exception, manager)
        manager.update(0.1)
        assert not t.alive
        assert t.success
        assert not t.last_blocking.alive
        assert not t.last_blocking.success
        assert t.result == 123


def main():
    import doctest
    doctest.testmod(task)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
