#!/usr/bin/env python

import abc
import types

import event


class Task(object):
    """
    Task object for continuous processing over time.

    :param args: positional arguments to be passed to :meth:`run` (optional)
    :param kwargs: keyword arguments to be passed to :meth:`run` (optional)
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, *args, **kwargs):
        """
        Create a task.
        """
        self._epoch = 0.0
        self._count = 0
        self._time = 0.0
        self._dtime = 0.0
        self._finalized = False
        self._running = True
        self._last_running = True
        self._last_call = 0.0
        self._next_call = 0.0
        self._unit_delayed = False
        self._iterator = self.run(*args, **kwargs)
        self._args = args
        self._kwargs = kwargs

    @property
    def alive(self):
        """
        Whether this task is alive or not.

        Alive task is running or suspended. Not alive task has finished its
        process written in :meth:`run` and already finalized.
        """
        return not self._finalized

    @property
    def running(self):
        """
        Whether this task is running or not.

        A task starts to run from the beginning, i.e., at the time of
        initialization. A task stop running when :meth:`suspend` is called or
        finalized. Stopped :attr:`alive` task may be resumed by calling
        :meth:`resume`.
        """
        return self._running

    @property
    def epoch(self):
        """
        The epoch time of the task in seconds. Internally used by the task
        manager.
        """
        return self._epoch

    @epoch.setter
    def epoch(self, value):
        self._epoch = value

    @property
    def count(self):
        """
        The number of times :meth:`run` is executed.
        """
        return self._count

    @property
    def time(self):
        """
        The elapsed time from the epoch.
        """
        return self._time

    @property
    def dtime(self):
        """
        The elapsed time from the last execution; the differential of
        :attr:`time`.
        """
        return self._dtime

    @property
    def unit(self):
        """
        The unit time.

        Return this unit time in :meth:`run` if you want it executed every
        :meth:`update`. Unlike returning 0, if you return :attr:`unit` the
        execution of :meth:`run` is suppressed until the next call of
        :meth:`update`. (In contrast, returning 0 makes multiple executions
        of :meth:`run` provided accumulated delays do not reach the current
        time.)  This behavior is useful and effective for rendering tasks.
        """
        return -1

    @abc.abstractmethod
    def run(self, *args, **kwargs):
        """
        The entry point for the task.

        :param args: positional arguments passed to :meth:`__init__`
        :param kwargs: keyword arguments passed to :meth:`__init__`

        This abstract method is the entry point for the task. You can write
        any code in it as far as it has at least one ``yield`` statement.

        The value of ``yield`` statement is treated as a delay; the code
        following the ``yield`` statement will be executed after the specified
        delay in seconds. All execution state including local variables are
        kept until the next execution.

        This method can have any number of positional parameters and keyword
        parameters. They receive the values of arguments which were passed
        to :meth:`__init__`; that is, if you initialize a task with the
        following code::

            class TaskA(task.Task):

                def run(self, a, b, c):
                    print a, b, c
                    yield self.unit

            t = TaskA(123, None, c='foo')
            t.update(0.0)

        You will get `'123 None foo'` on the standard output.

        When finishing the execution of this method, :meth:`finalize` will be
        called.
        """
        pass

    def finalize(self, *args, **kwargs):
        """
        The finalizer of the task.

        :param args: positional arguments passed to :meth:`__init__`
        :param kwargs: keyword arguments passed to :meth:`__init__`

        This method is called right after the task is finished; that is, when
        no more code is left to run, or, when this task is removed via
        :meth:`TaskManager.remove`. You can omit to implement this method if
        you have nothing special to clean up explicitly.

        Note that this method receives the same arguments as those :meth:`run`
        does. Therefore you should use the same signature for both methods::

            class TaskA(task.Task):

                def run(self, a, b, c):
                    # do something
                    pass

                def finalize(self, a, b, c):
                    # do cleanup
                    pass

        If you are going to implement your custom task manager, do not call
        this method directly; call :meth:`call_finalizer` instead.
        """
        pass

    def call_finalizer(self):
        """
        Call the finalizer, changing the internal state properly.

        If you are going to implement your custom task manager, call this
        method instead of calling :meth:`finalize` directly.
        """
        if self._finalized:
            return
        self.finalize(*self._args, **self._kwargs)
        self._finalized = True
        self.suspend()
        self.finished()

    def suspend(self):
        """
        Suspend execution of this task.

        A call of :meth:`suspend` is considered to be done right after the
        previous call of :meth:`update`.
        """
        self._last_running = self._running
        self._running = False
        if self._last_running:
            self._last_call = self._time

    def resume(self):
        """
        Resume execution of this task.

        :raises StopIteration: when the task is finished

        A call of :meth:`resume` is considered to be done right after the
        previous call of :meth:`update`.
        """
        if self._finalized:
            raise StopIteration()
        self._last_running = self._running
        self._running = True
        if not self._last_running:
            self._next_call = self._time + (self._next_call - self._last_call)

    def update(self, current):
        """
        Update the task. Internally used by the task manager.

        :param current: current time in seconds
        :returns: task object which suspends this task; None otherwise
        :raises StopIteration: when the task is finished
        """
        if self._finalized:
            raise StopIteration()
        self._time = current - self.epoch
        if not self._running:
            return
        while self._time >= self._next_call:
            try:
                self._count += 1
                self._dtime = self._time - self._last_call
                self._last_call = self._time
                if self._unit_delayed:
                    self._next_call += self._dtime
                    self._unit_delayed = False
                delay = self._iterator.next()
                if delay == self.unit:
                    self._unit_delayed = True
                    return
                elif isinstance(delay, Task):
                    self.suspend()
                    return delay
                self._next_call += delay
            except StopIteration, e:
                self.call_finalizer()
                raise e

    _finished = event.Event()

    @property
    def finished(self):
        """
        Event raised when the task has finished its process.

        This event takes no parameter.
        """
        return self._finished

    @finished.setter
    def finished(self, value):
        pass


class FunctionTask(Task):
    """
    Task object for a function.

    :param run: function object to be called within :meth:`run`
    :param args: positional arguments to be passed to :meth:`run` (optional)
    :param kwargs: keyword arguments to be passed to :meth:`run` (optional)
    """

    def __init__(self, run, *args, **kwargs):
        self._run = run
        super(FunctionTask, self).__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        return self._run(self, *args, **kwargs)


class TaskManager(object):
    """
    Task manager, manages a collection of :class:`Task`.

    :param epoch: epoch time in seconds
    """

    def __init__(self, epoch):
        """
        Create a task manager.
        """
        self._tasks = []
        self._pending_tasks = []
        self._epoch = epoch
        self._time = epoch
        self._running_count = 0

    @property
    def epoch(self):
        """
        The epoch time in seconds.
        """
        return self._epoch

    @property
    def time(self):
        """
        The elapsed time from the epoch.
        """
        return self._time

    @property
    def running_count(self):
        # TODO: Test this
        return self._running_count

    def add(self, task, *args, **kwargs):
        """
        Add a task.

        :param task: task or function to add
        :param args: positional arguments to be passed to :meth:`Task.run`
            (optional)
        :param kwargs: keyword arguments to be passed to :meth:`Task.run`
            (optional)
        :returns: task object

        This method adds *task* to the collection of registered tasks. When
        :meth:`update` is called, registered tasks are updated in the order
        they were added.

        The first parameter *task* may be a task object, a function object or
        a method object. If *task* is a function or method object, a new
        :class:`FunctionTask` object will be created for it and added. You
        can use the return value to remove the task from the manager::

            def do_task(task, a, b, c):
                # do something
                pass

            manager = task.TaskManager(0.0)
            t = manager.add(do_task, 123, 456.789, None)
            # do something
            manager.remove(t)
        """
        if task in self._tasks:
            # TODO: Test this (returning task, not None)
            return task
        if isinstance(task, (types.FunctionType, types.MethodType)):
            task = FunctionTask(task, *args, **kwargs)
        task.epoch = self._time
        self._tasks.append(task)
        self._add_pending(task)
        return task

    def remove(self, task):
        """
        Remove a task.

        :param task: task to remove
        """
        try:
            index = self._tasks.index(task)
        except ValueError:
            return
        del self._tasks[index]
        task.call_finalizer()

    def clear(self):
        # TODO: Test this
        for task in self._tasks:
            task.call_finalizer()
        del self._tasks[:]

    def _add_pending(self, task):
        self._pending_tasks.append(task)

    def _get_pending(self):
        pending_tasks = self._pending_tasks
        self._clear_pending()
        return pending_tasks

    def _clear_pending(self):
        self._pending_tasks = []

    def _get_tasks(self):
        self._clear_pending()
        return self._tasks

    def update(self, current):
        """
        Update all tasks.

        :param current: current time in seconds
        """
        self._time = current
        tasks = self._get_tasks()
        to_be_removed = []
        running_count = 0
        while len(tasks) > 0:
            for task in tasks:
                try:
                    blocking_task = task.update(current)
                    running_count += 1 if task.alive and task.running else 0
                    if blocking_task:
                        def make_resume(task):
                            def resume(sender):
                                task.resume()
                                self._add_pending(task)
                            resume.task = task
                            return resume
                        blocking_task.finished += make_resume(task)
                except StopIteration:
                    to_be_removed.append(task)
            tasks = self._get_pending()
        self._tasks = filter(lambda task: task not in to_be_removed,
                             self._tasks)
        self._running_count = running_count

    @property
    def tasks(self):
        # TODO: Test this
        return self._tasks

    @property
    def empty(self):
        # TODO: Add tests.
        return not self._tasks

    @property
    def __len__(self):
        # TODO: Test this
        return len(self._tasks)


if __name__ == '__main__':
    import task_test
    task_test.main()
