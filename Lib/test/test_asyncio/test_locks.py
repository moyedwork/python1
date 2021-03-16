"""Tests for lock.py"""

import unittest
from unittest import mock
import re

import asyncio
from test.test_asyncio import utils as test_utils
import functools

STR_RGX_REPR = (
    r'^<(?P<class>.*?) object at (?P<address>.*?)'
    r'\[(?P<extras>'
    r'(set|unset|locked|unlocked)(, value:\d)?(, waiters:\d+)?'
    r'(, count:\d+\/\d+)?(, (set|unset))?(, state:(-2|-1|0|1))?' # new line dedicated to repr barrier
    r')\]>\Z'
)
RGX_REPR = re.compile(STR_RGX_REPR)


def tearDownModule():
    asyncio.set_event_loop_policy(None)


class LockTests(test_utils.TestCase):

    def setUp(self):
        super().setUp()
        self.loop = self.new_test_loop()

    def test_repr(self):
        lock = asyncio.Lock()
        self.assertTrue(repr(lock).endswith('[unlocked]>'))
        self.assertTrue(RGX_REPR.match(repr(lock)))

        self.loop.run_until_complete(lock.acquire())
        self.assertTrue(repr(lock).endswith('[locked]>'))
        self.assertTrue(RGX_REPR.match(repr(lock)))

    def test_lock(self):
        lock = asyncio.Lock()

        with self.assertWarns(DeprecationWarning):
            @asyncio.coroutine
            def acquire_lock():
                return (yield from lock)

        with self.assertRaisesRegex(
            TypeError,
            "object is not iterable"
        ):
            self.loop.run_until_complete(acquire_lock())

        self.assertFalse(lock.locked())

    def test_lock_doesnt_accept_loop_parameter(self):
        primitives_cls = [
            asyncio.Lock,
            asyncio.Condition,
            asyncio.Event,
            asyncio.Semaphore,
            asyncio.BoundedSemaphore,
        ]

        for cls in primitives_cls:
            with self.assertRaisesRegex(
                TypeError,
                rf'As of 3.10, the \*loop\* parameter was removed from '
                rf'{cls.__name__}\(\) since it is no longer necessary'
            ):
                cls(loop=self.loop)

        # Barrier object has a positional paramater
        # so tests alone
        cls = asyncio.Barrier
        with self.assertRaisesRegex(
            TypeError,
            rf'As of 3.10, the \*loop\* parameter was removed from '
            rf'{cls.__name__}\(\) since it is no longer necessary'
        ):
            cls(1, loop=self.loop)

    def test_lock_by_with_statement(self):
        loop = asyncio.new_event_loop()  # don't use TestLoop quirks
        self.set_event_loop(loop)
        primitives = [
            asyncio.Lock(),
            asyncio.Condition(),
            asyncio.Semaphore(),
            asyncio.BoundedSemaphore(),
        ]

        with self.assertWarns(DeprecationWarning):
            @asyncio.coroutine
            def test(lock):
                yield from asyncio.sleep(0.01)
                self.assertFalse(lock.locked())
                with self.assertRaisesRegex(
                    TypeError,
                    "object is not iterable"
                ):
                    with (yield from lock):
                        pass
                self.assertFalse(lock.locked())

        for primitive in primitives:
            loop.run_until_complete(test(primitive))
            self.assertFalse(primitive.locked())

    def test_acquire(self):
        lock = asyncio.Lock()
        result = []

        self.assertTrue(self.loop.run_until_complete(lock.acquire()))

        async def c1(result):
            if await lock.acquire():
                result.append(1)
            return True

        async def c2(result):
            if await lock.acquire():
                result.append(2)
            return True

        async def c3(result):
            if await lock.acquire():
                result.append(3)
            return True

        t1 = self.loop.create_task(c1(result))
        t2 = self.loop.create_task(c2(result))

        test_utils.run_briefly(self.loop)
        self.assertEqual([], result)

        lock.release()
        test_utils.run_briefly(self.loop)
        self.assertEqual([1], result)

        test_utils.run_briefly(self.loop)
        self.assertEqual([1], result)

        t3 = self.loop.create_task(c3(result))

        lock.release()
        test_utils.run_briefly(self.loop)
        self.assertEqual([1, 2], result)

        lock.release()
        test_utils.run_briefly(self.loop)
        self.assertEqual([1, 2, 3], result)

        self.assertTrue(t1.done())
        self.assertTrue(t1.result())
        self.assertTrue(t2.done())
        self.assertTrue(t2.result())
        self.assertTrue(t3.done())
        self.assertTrue(t3.result())

    def test_acquire_cancel(self):
        lock = asyncio.Lock()
        self.assertTrue(self.loop.run_until_complete(lock.acquire()))

        task = self.loop.create_task(lock.acquire())
        self.loop.call_soon(task.cancel)
        self.assertRaises(
            asyncio.CancelledError,
            self.loop.run_until_complete, task)
        self.assertFalse(lock._waiters)

    def test_cancel_race(self):
        # Several tasks:
        # - A acquires the lock
        # - B is blocked in acquire()
        # - C is blocked in acquire()
        #
        # Now, concurrently:
        # - B is cancelled
        # - A releases the lock
        #
        # If B's waiter is marked cancelled but not yet removed from
        # _waiters, A's release() call will crash when trying to set
        # B's waiter; instead, it should move on to C's waiter.

        # Setup: A has the lock, b and c are waiting.
        lock = asyncio.Lock()

        async def lockit(name, blocker):
            await lock.acquire()
            try:
                if blocker is not None:
                    await blocker
            finally:
                lock.release()

        fa = self.loop.create_future()
        ta = self.loop.create_task(lockit('A', fa))
        test_utils.run_briefly(self.loop)
        self.assertTrue(lock.locked())
        tb = self.loop.create_task(lockit('B', None))
        test_utils.run_briefly(self.loop)
        self.assertEqual(len(lock._waiters), 1)
        tc = self.loop.create_task(lockit('C', None))
        test_utils.run_briefly(self.loop)
        self.assertEqual(len(lock._waiters), 2)

        # Create the race and check.
        # Without the fix this failed at the last assert.
        fa.set_result(None)
        tb.cancel()
        self.assertTrue(lock._waiters[0].cancelled())
        test_utils.run_briefly(self.loop)
        self.assertFalse(lock.locked())
        self.assertTrue(ta.done())
        self.assertTrue(tb.cancelled())
        self.assertTrue(tc.done())

    def test_cancel_release_race(self):
        # Issue 32734
        # Acquire 4 locks, cancel second, release first
        # and 2 locks are taken at once.
        lock = asyncio.Lock()
        lock_count = 0
        call_count = 0

        async def lockit():
            nonlocal lock_count
            nonlocal call_count
            call_count += 1
            await lock.acquire()
            lock_count += 1

        async def lockandtrigger():
            await lock.acquire()
            self.loop.call_soon(trigger)

        def trigger():
            t1.cancel()
            lock.release()

        t0 = self.loop.create_task(lockandtrigger())
        t1 = self.loop.create_task(lockit())
        t2 = self.loop.create_task(lockit())
        t3 = self.loop.create_task(lockit())

        # First loop acquires all
        test_utils.run_briefly(self.loop)
        self.assertTrue(t0.done())

        # Second loop calls trigger
        test_utils.run_briefly(self.loop)
        # Third loop calls cancellation
        test_utils.run_briefly(self.loop)

        # Make sure only one lock was taken
        self.assertEqual(lock_count, 1)
        # While 3 calls were made to lockit()
        self.assertEqual(call_count, 3)
        self.assertTrue(t1.cancelled() and t2.done())

        # Cleanup the task that is stuck on acquire.
        t3.cancel()
        test_utils.run_briefly(self.loop)
        self.assertTrue(t3.cancelled())

    def test_finished_waiter_cancelled(self):
        lock = asyncio.Lock()

        ta = self.loop.create_task(lock.acquire())
        test_utils.run_briefly(self.loop)
        self.assertTrue(lock.locked())

        tb = self.loop.create_task(lock.acquire())
        test_utils.run_briefly(self.loop)
        self.assertEqual(len(lock._waiters), 1)

        # Create a second waiter, wake up the first, and cancel it.
        # Without the fix, the second was not woken up.
        tc = self.loop.create_task(lock.acquire())
        lock.release()
        tb.cancel()
        test_utils.run_briefly(self.loop)

        self.assertTrue(lock.locked())
        self.assertTrue(ta.done())
        self.assertTrue(tb.cancelled())

    def test_release_not_acquired(self):
        lock = asyncio.Lock()

        self.assertRaises(RuntimeError, lock.release)

    def test_release_no_waiters(self):
        lock = asyncio.Lock()
        self.loop.run_until_complete(lock.acquire())
        self.assertTrue(lock.locked())

        lock.release()
        self.assertFalse(lock.locked())

    def test_context_manager(self):
        async def f():
            lock = asyncio.Lock()
            self.assertFalse(lock.locked())

            async with lock:
                self.assertTrue(lock.locked())

            self.assertFalse(lock.locked())

        self.loop.run_until_complete(f())


class EventTests(test_utils.TestCase):

    def setUp(self):
        super().setUp()
        self.loop = self.new_test_loop()

    def test_repr(self):
        ev = asyncio.Event()
        self.assertTrue(repr(ev).endswith('[unset]>'))
        match = RGX_REPR.match(repr(ev))
        self.assertEqual(match.group('extras'), 'unset')

        ev.set()
        self.assertTrue(repr(ev).endswith('[set]>'))
        self.assertTrue(RGX_REPR.match(repr(ev)))

        ev._waiters.append(mock.Mock())
        self.assertTrue('waiters:1' in repr(ev))
        self.assertTrue(RGX_REPR.match(repr(ev)))

    def test_wait(self):
        ev = asyncio.Event()
        self.assertFalse(ev.is_set())

        result = []

        async def c1(result):
            if await ev.wait():
                result.append(1)

        async def c2(result):
            if await ev.wait():
                result.append(2)

        async def c3(result):
            if await ev.wait():
                result.append(3)

        t1 = self.loop.create_task(c1(result))
        t2 = self.loop.create_task(c2(result))

        test_utils.run_briefly(self.loop)
        self.assertEqual([], result)

        t3 = self.loop.create_task(c3(result))

        ev.set()
        test_utils.run_briefly(self.loop)
        self.assertEqual([3, 1, 2], result)

        self.assertTrue(t1.done())
        self.assertIsNone(t1.result())
        self.assertTrue(t2.done())
        self.assertIsNone(t2.result())
        self.assertTrue(t3.done())
        self.assertIsNone(t3.result())

    def test_wait_on_set(self):
        ev = asyncio.Event()
        ev.set()

        res = self.loop.run_until_complete(ev.wait())
        self.assertTrue(res)

    def test_wait_cancel(self):
        ev = asyncio.Event()

        wait = self.loop.create_task(ev.wait())
        self.loop.call_soon(wait.cancel)
        self.assertRaises(
            asyncio.CancelledError,
            self.loop.run_until_complete, wait)
        self.assertFalse(ev._waiters)

    def test_clear(self):
        ev = asyncio.Event()
        self.assertFalse(ev.is_set())

        ev.set()
        self.assertTrue(ev.is_set())

        ev.clear()
        self.assertFalse(ev.is_set())

    def test_clear_with_waiters(self):
        ev = asyncio.Event()
        result = []

        async def c1(result):
            if await ev.wait():
                result.append(1)
            return True

        t = self.loop.create_task(c1(result))
        test_utils.run_briefly(self.loop)
        self.assertEqual([], result)

        ev.set()
        ev.clear()
        self.assertFalse(ev.is_set())

        ev.set()
        ev.set()
        self.assertEqual(1, len(ev._waiters))

        test_utils.run_briefly(self.loop)
        self.assertEqual([1], result)
        self.assertEqual(0, len(ev._waiters))

        self.assertTrue(t.done())
        self.assertTrue(t.result())


class ConditionTests(test_utils.TestCase):

    def setUp(self):
        super().setUp()
        self.loop = self.new_test_loop()

    def test_wait(self):
        cond = asyncio.Condition()
        result = []

        async def c1(result):
            await cond.acquire()
            if await cond.wait():
                result.append(1)
            return True

        async def c2(result):
            await cond.acquire()
            if await cond.wait():
                result.append(2)
            return True

        async def c3(result):
            await cond.acquire()
            if await cond.wait():
                result.append(3)
            return True

        t1 = self.loop.create_task(c1(result))
        t2 = self.loop.create_task(c2(result))
        t3 = self.loop.create_task(c3(result))

        test_utils.run_briefly(self.loop)
        self.assertEqual([], result)
        self.assertFalse(cond.locked())

        self.assertTrue(self.loop.run_until_complete(cond.acquire()))
        cond.notify()
        test_utils.run_briefly(self.loop)
        self.assertEqual([], result)
        self.assertTrue(cond.locked())

        cond.release()
        test_utils.run_briefly(self.loop)
        self.assertEqual([1], result)
        self.assertTrue(cond.locked())

        cond.notify(2)
        test_utils.run_briefly(self.loop)
        self.assertEqual([1], result)
        self.assertTrue(cond.locked())

        cond.release()
        test_utils.run_briefly(self.loop)
        self.assertEqual([1, 2], result)
        self.assertTrue(cond.locked())

        cond.release()
        test_utils.run_briefly(self.loop)
        self.assertEqual([1, 2, 3], result)
        self.assertTrue(cond.locked())

        self.assertTrue(t1.done())
        self.assertTrue(t1.result())
        self.assertTrue(t2.done())
        self.assertTrue(t2.result())
        self.assertTrue(t3.done())
        self.assertTrue(t3.result())

    def test_wait_cancel(self):
        cond = asyncio.Condition()
        self.loop.run_until_complete(cond.acquire())

        wait = self.loop.create_task(cond.wait())
        self.loop.call_soon(wait.cancel)
        self.assertRaises(
            asyncio.CancelledError,
            self.loop.run_until_complete, wait)
        self.assertFalse(cond._waiters)
        self.assertTrue(cond.locked())

    def test_wait_cancel_contested(self):
        cond = asyncio.Condition()

        self.loop.run_until_complete(cond.acquire())
        self.assertTrue(cond.locked())

        wait_task = self.loop.create_task(cond.wait())
        test_utils.run_briefly(self.loop)
        self.assertFalse(cond.locked())

        # Notify, but contest the lock before cancelling
        self.loop.run_until_complete(cond.acquire())
        self.assertTrue(cond.locked())
        cond.notify()
        self.loop.call_soon(wait_task.cancel)
        self.loop.call_soon(cond.release)

        try:
            self.loop.run_until_complete(wait_task)
        except asyncio.CancelledError:
            # Should not happen, since no cancellation points
            pass

        self.assertTrue(cond.locked())

    def test_wait_cancel_after_notify(self):
        # See bpo-32841
        waited = False

        cond = asyncio.Condition()
        cond._loop = self.loop

        async def wait_on_cond():
            nonlocal waited
            async with cond:
                waited = True  # Make sure this area was reached
                await cond.wait()

        waiter = asyncio.ensure_future(wait_on_cond(), loop=self.loop)
        test_utils.run_briefly(self.loop)  # Start waiting

        self.loop.run_until_complete(cond.acquire())
        cond.notify()
        test_utils.run_briefly(self.loop)  # Get to acquire()
        waiter.cancel()
        test_utils.run_briefly(self.loop)  # Activate cancellation
        cond.release()
        test_utils.run_briefly(self.loop)  # Cancellation should occur

        self.assertTrue(waiter.cancelled())
        self.assertTrue(waited)

    def test_wait_unacquired(self):
        cond = asyncio.Condition()
        self.assertRaises(
            RuntimeError,
            self.loop.run_until_complete, cond.wait())

    def test_wait_for(self):
        cond = asyncio.Condition()
        presult = False

        def predicate():
            return presult

        result = []

        async def c1(result):
            await cond.acquire()
            if await cond.wait_for(predicate):
                result.append(1)
                cond.release()
            return True

        t = self.loop.create_task(c1(result))

        test_utils.run_briefly(self.loop)
        self.assertEqual([], result)

        self.loop.run_until_complete(cond.acquire())
        cond.notify()
        cond.release()
        test_utils.run_briefly(self.loop)
        self.assertEqual([], result)

        presult = True
        self.loop.run_until_complete(cond.acquire())
        cond.notify()
        cond.release()
        test_utils.run_briefly(self.loop)
        self.assertEqual([1], result)

        self.assertTrue(t.done())
        self.assertTrue(t.result())

    def test_wait_for_unacquired(self):
        cond = asyncio.Condition()

        # predicate can return true immediately
        res = self.loop.run_until_complete(cond.wait_for(lambda: [1, 2, 3]))
        self.assertEqual([1, 2, 3], res)

        self.assertRaises(
            RuntimeError,
            self.loop.run_until_complete,
            cond.wait_for(lambda: False))

    def test_notify(self):
        cond = asyncio.Condition()
        result = []

        async def c1(result):
            await cond.acquire()
            if await cond.wait():
                result.append(1)
                cond.release()
            return True

        async def c2(result):
            await cond.acquire()
            if await cond.wait():
                result.append(2)
                cond.release()
            return True

        async def c3(result):
            await cond.acquire()
            if await cond.wait():
                result.append(3)
                cond.release()
            return True

        t1 = self.loop.create_task(c1(result))
        t2 = self.loop.create_task(c2(result))
        t3 = self.loop.create_task(c3(result))

        test_utils.run_briefly(self.loop)
        self.assertEqual([], result)

        self.loop.run_until_complete(cond.acquire())
        cond.notify(1)
        cond.release()
        test_utils.run_briefly(self.loop)
        self.assertEqual([1], result)

        self.loop.run_until_complete(cond.acquire())
        cond.notify(1)
        cond.notify(2048)
        cond.release()
        test_utils.run_briefly(self.loop)
        self.assertEqual([1, 2, 3], result)

        self.assertTrue(t1.done())
        self.assertTrue(t1.result())
        self.assertTrue(t2.done())
        self.assertTrue(t2.result())
        self.assertTrue(t3.done())
        self.assertTrue(t3.result())

    def test_notify_all(self):
        cond = asyncio.Condition()

        result = []

        async def c1(result):
            await cond.acquire()
            if await cond.wait():
                result.append(1)
                cond.release()
            return True

        async def c2(result):
            await cond.acquire()
            if await cond.wait():
                result.append(2)
                cond.release()
            return True

        t1 = self.loop.create_task(c1(result))
        t2 = self.loop.create_task(c2(result))

        test_utils.run_briefly(self.loop)
        self.assertEqual([], result)

        self.loop.run_until_complete(cond.acquire())
        cond.notify_all()
        cond.release()
        test_utils.run_briefly(self.loop)
        self.assertEqual([1, 2], result)

        self.assertTrue(t1.done())
        self.assertTrue(t1.result())
        self.assertTrue(t2.done())
        self.assertTrue(t2.result())

    def test_notify_unacquired(self):
        cond = asyncio.Condition()
        self.assertRaises(RuntimeError, cond.notify)

    def test_notify_all_unacquired(self):
        cond = asyncio.Condition()
        self.assertRaises(RuntimeError, cond.notify_all)

    def test_repr(self):
        cond = asyncio.Condition()
        self.assertTrue('unlocked' in repr(cond))
        self.assertTrue(RGX_REPR.match(repr(cond)))

        self.loop.run_until_complete(cond.acquire())
        self.assertTrue('locked' in repr(cond))

        cond._waiters.append(mock.Mock())
        self.assertTrue('waiters:1' in repr(cond))
        self.assertTrue(RGX_REPR.match(repr(cond)))

        cond._waiters.append(mock.Mock())
        self.assertTrue('waiters:2' in repr(cond))
        self.assertTrue(RGX_REPR.match(repr(cond)))

    def test_context_manager(self):
        async def f():
            cond = asyncio.Condition()
            self.assertFalse(cond.locked())
            async with cond:
                self.assertTrue(cond.locked())
            self.assertFalse(cond.locked())

        self.loop.run_until_complete(f())

    def test_explicit_lock(self):
        lock = asyncio.Lock()
        cond = asyncio.Condition(lock)

        self.assertIs(cond._lock, lock)
        self.assertIs(cond._loop, lock._loop)

    def test_ambiguous_loops(self):
        loop = self.new_test_loop()
        self.addCleanup(loop.close)

        lock = asyncio.Lock()
        lock._loop = loop

        async def _create_condition():
            with self.assertRaises(ValueError):
                asyncio.Condition(lock)

        self.loop.run_until_complete(_create_condition())

    def test_timeout_in_block(self):
        loop = asyncio.new_event_loop()
        self.addCleanup(loop.close)

        async def task_timeout():
            condition = asyncio.Condition()
            async with condition:
                with self.assertRaises(asyncio.TimeoutError):
                    await asyncio.wait_for(condition.wait(), timeout=0.5)

        loop.run_until_complete(task_timeout())


class SemaphoreTests(test_utils.TestCase):

    def setUp(self):
        super().setUp()
        self.loop = self.new_test_loop()

    def test_initial_value_zero(self):
        sem = asyncio.Semaphore(0)
        self.assertTrue(sem.locked())

    def test_repr(self):
        sem = asyncio.Semaphore()
        self.assertTrue(repr(sem).endswith('[unlocked, value:1]>'))
        self.assertTrue(RGX_REPR.match(repr(sem)))

        self.loop.run_until_complete(sem.acquire())
        self.assertTrue(repr(sem).endswith('[locked]>'))
        self.assertTrue('waiters' not in repr(sem))
        self.assertTrue(RGX_REPR.match(repr(sem)))

        sem._waiters.append(mock.Mock())
        self.assertTrue('waiters:1' in repr(sem))
        self.assertTrue(RGX_REPR.match(repr(sem)))

        sem._waiters.append(mock.Mock())
        self.assertTrue('waiters:2' in repr(sem))
        self.assertTrue(RGX_REPR.match(repr(sem)))

    def test_semaphore(self):
        sem = asyncio.Semaphore()
        self.assertEqual(1, sem._value)

        with self.assertWarns(DeprecationWarning):
            @asyncio.coroutine
            def acquire_lock():
                return (yield from sem)

        with self.assertRaisesRegex(
            TypeError,
            "'Semaphore' object is not iterable",
        ):
            self.loop.run_until_complete(acquire_lock())

        self.assertFalse(sem.locked())
        self.assertEqual(1, sem._value)

    def test_semaphore_value(self):
        self.assertRaises(ValueError, asyncio.Semaphore, -1)

    def test_acquire(self):
        sem = asyncio.Semaphore(3)
        result = []

        self.assertTrue(self.loop.run_until_complete(sem.acquire()))
        self.assertTrue(self.loop.run_until_complete(sem.acquire()))
        self.assertFalse(sem.locked())

        async def c1(result):
            await sem.acquire()
            result.append(1)
            return True

        async def c2(result):
            await sem.acquire()
            result.append(2)
            return True

        async def c3(result):
            await sem.acquire()
            result.append(3)
            return True

        async def c4(result):
            await sem.acquire()
            result.append(4)
            return True

        t1 = self.loop.create_task(c1(result))
        t2 = self.loop.create_task(c2(result))
        t3 = self.loop.create_task(c3(result))

        test_utils.run_briefly(self.loop)
        self.assertEqual([1], result)
        self.assertTrue(sem.locked())
        self.assertEqual(2, len(sem._waiters))
        self.assertEqual(0, sem._value)

        t4 = self.loop.create_task(c4(result))

        sem.release()
        sem.release()
        self.assertEqual(2, sem._value)

        test_utils.run_briefly(self.loop)
        self.assertEqual(0, sem._value)
        self.assertEqual(3, len(result))
        self.assertTrue(sem.locked())
        self.assertEqual(1, len(sem._waiters))
        self.assertEqual(0, sem._value)

        self.assertTrue(t1.done())
        self.assertTrue(t1.result())
        race_tasks = [t2, t3, t4]
        done_tasks = [t for t in race_tasks if t.done() and t.result()]
        self.assertTrue(2, len(done_tasks))

        # cleanup locked semaphore
        sem.release()
        self.loop.run_until_complete(asyncio.gather(*race_tasks))

    def test_acquire_cancel(self):
        sem = asyncio.Semaphore()
        self.loop.run_until_complete(sem.acquire())

        acquire = self.loop.create_task(sem.acquire())
        self.loop.call_soon(acquire.cancel)
        self.assertRaises(
            asyncio.CancelledError,
            self.loop.run_until_complete, acquire)
        self.assertTrue((not sem._waiters) or
                        all(waiter.done() for waiter in sem._waiters))

    def test_acquire_cancel_before_awoken(self):
        sem = asyncio.Semaphore(value=0)

        t1 = self.loop.create_task(sem.acquire())
        t2 = self.loop.create_task(sem.acquire())
        t3 = self.loop.create_task(sem.acquire())
        t4 = self.loop.create_task(sem.acquire())

        test_utils.run_briefly(self.loop)

        sem.release()
        t1.cancel()
        t2.cancel()

        test_utils.run_briefly(self.loop)
        num_done = sum(t.done() for t in [t3, t4])
        self.assertEqual(num_done, 1)

        t3.cancel()
        t4.cancel()
        test_utils.run_briefly(self.loop)

    def test_acquire_hang(self):
        sem = asyncio.Semaphore(value=0)

        t1 = self.loop.create_task(sem.acquire())
        t2 = self.loop.create_task(sem.acquire())

        test_utils.run_briefly(self.loop)

        sem.release()
        t1.cancel()

        test_utils.run_briefly(self.loop)
        self.assertTrue(sem.locked())

    def test_release_not_acquired(self):
        sem = asyncio.BoundedSemaphore()

        self.assertRaises(ValueError, sem.release)

    def test_release_no_waiters(self):
        sem = asyncio.Semaphore()
        self.loop.run_until_complete(sem.acquire())
        self.assertTrue(sem.locked())

        sem.release()
        self.assertFalse(sem.locked())


class BarrierTests(test_utils.TestCase):
    """
    Tests for Barrier objects.
    """
    def setUp(self):
        super().setUp()
        self.loop = self.new_test_loop()
        self.N = 5

    async def run_coros(self, n, coro):
        tasks = [self.loop.create_task(coro()) for _ in range(n)]
        res = await asyncio.gather(*tasks)
        return res, tasks

    def cancel_coros(self):
        for task in asyncio.all_tasks(self.loop):
            task.cancel()
        test_utils.run_briefly(self.loop)

    def test_repr(self):
        async def coro():
            try:
                i = await barrier.wait()
            except:
                ...
            else:
                return await asyncio.sleep(1, True)

        self.N = 1011001
        barrier = asyncio.Barrier(self.N)
        self.assertTrue("[unset," in repr(barrier))
        self.assertTrue(f"count:0/{str(self.N)}" in repr(barrier))
        self.assertTrue(RGX_REPR.match(repr(barrier)))
        self.assertTrue(repr(barrier).endswith('unset, state:0]>'))

        nb_waits = 3
        tasks = []
        for _ in range(nb_waits):
            tasks.append(self.loop.create_task(coro()))
        test_utils.run_briefly(self.loop)
        self.assertTrue("[unset," in repr(barrier))
        self.assertTrue(RGX_REPR.match(repr(barrier)))
        self.assertTrue(f"count:{nb_waits}/{self.N}" in repr(barrier))
        self.assertTrue(repr(barrier).endswith('unset, state:0]>'))

        barrier.reset()
        self.assertTrue(RGX_REPR.match(repr(barrier)))
        self.assertTrue("[set," in repr(barrier))
        self.assertTrue(f"count:{nb_waits}/{self.N}" in repr(barrier))
        self.assertTrue(repr(barrier).endswith('unset, state:-1]>'))
        test_utils.run_briefly(self.loop)
        self.assertTrue(RGX_REPR.match(repr(barrier)))
        self.assertTrue("[unset," in repr(barrier))
        self.assertTrue(f"count:0/{self.N}" in repr(barrier))
        self.assertTrue(repr(barrier).endswith('set, state:0]>'))
        test_utils.run_briefly(self.loop)

        barrier.abort()
        test_utils.run_briefly(self.loop)
        self.assertTrue(RGX_REPR.match(repr(barrier)))
        self.assertTrue(f"0/{self.N}" in repr(barrier))
        self.assertTrue(repr(barrier).endswith(':-2]>'))

        self.cancel_coros()

    def test_init(self):
        self.assertRaises(ValueError, lambda: asyncio.Barrier(0))
        self.assertRaises(ValueError, lambda: asyncio.Barrier(-4))

    def test_wait_task_once(self):
        self.N = 1
        barrier = asyncio.Barrier(self.N)
        self.assertEqual(barrier.n_waiting, 0)
        r1 = self.loop.run_until_complete(barrier.wait())
        self.assertEqual(barrier.n_waiting, 0)
        r2 = self.loop.run_until_complete(barrier.wait())
        self.assertEqual(barrier.n_waiting, 0)
        self.assertEqual(r1, r2)
        self.assertFalse(barrier.broken)

    def test_wait_task_by_task(self):
        self.N = 3
        barrier = asyncio.Barrier(self.N)
        self.assertEqual(barrier.n_waiting, 0)
        self.loop.create_task(barrier.wait())
        test_utils.run_briefly(self.loop)
        self.assertEqual(barrier.n_waiting, 1)
        self.loop.create_task(barrier.wait())
        test_utils.run_briefly(self.loop)
        self.assertEqual(barrier.n_waiting, 2)
        self.loop.create_task(barrier.wait())
        test_utils.run_briefly(self.loop)
        self.assertEqual(barrier.n_waiting, 0)
        self.assertFalse(barrier.broken)

    def test_wait_tasks_twice(self):
        results = []
        async def coro():
            await barrier.wait()
            results.append(True)
            await barrier.wait()
            results.append(False)

        barrier = asyncio.Barrier(self.N)
        self.loop.run_until_complete(self.run_coros(self.N, coro))
        self.assertEqual(len(results), self.N*2)
        self.assertEqual(results.count(True), self.N)
        self.assertEqual(results.count(False), self.N)
        self.assertFalse(barrier.broken)
        self.assertEqual(barrier.n_waiting, 0)

    def test_wait_return_from_wait(self):
        results1 = []
        results2 = []
        async def coro():
            await barrier.wait()
            results1.append(True)
            i = await barrier.wait()
            results2.append(True)
            return i

        barrier = asyncio.Barrier(self.N)
        res = self.loop.run_until_complete(self.run_coros(self.N, coro))
        self.assertEqual(len(results1), self.N)
        self.assertTrue(all(results1))
        self.assertEqual(len(results2), self.N)
        self.assertTrue(all(results2))
        self.assertEqual(sum(res[0]), sum(range(self.N)))
        self.assertEqual(barrier.n_waiting, 0)
        self.assertFalse(barrier.broken)


    def test_wait_repeat_more(self, more=5):
        async def coro(result, value):
            ret = await barrier.wait()
            result.append(value)

        results = [[] for _ in range(more)]
        barrier = asyncio.Barrier(self.N)
        for i in range(more):
            _ = [self.loop.create_task(coro(results[i], value)) for value in range(self.N)]
            test_utils.run_briefly(self.loop)

            self.assertEqual(len(results[i]), self.N)
            self.assertEqual(sum(results[i]), sum(range(self.N)))
            if i > 0:
                self.assertEqual(sum(results[i]), sum(results[i-1]))
            self.assertEqual(barrier.n_waiting, 0)
            self.assertFalse(barrier.broken)

    def test_wait_state_draining(self):
        result = []
        state = []
        async def coro():
            i = await barrier.wait()
            if i == 0:
                result.append(True)
                # Do we need to add a Barrie.draining() property ?
                state.append(repr(barrier).endswith("state:1]>"))

        rest = self.N-1
        nb_tasks = self.N + rest
        barrier = asyncio.Barrier(self.N)
        for _ in range(nb_tasks):
            self.loop.create_task(coro())
        for _ in range((nb_tasks//self.N)+1):
            test_utils.run_briefly(self.loop)
        self.assertEqual(len(result), nb_tasks//self.N)
        self.assertTrue(all(result))
        self.assertTrue(all(state))
        self.assertEqual(barrier.n_waiting, rest)
        self.assertFalse(barrier.broken)

        self.cancel_coros()

    def test_wait_tasks_cancel_one_task(self):
        results = []
        async def coro():
            await barrier.wait()
            results.append(True)

        self.N=3
        barrier = asyncio.Barrier(self.N)
        t1 = self.loop.create_task(coro())
        test_utils.run_briefly(self.loop)
        self.assertEqual(barrier.n_waiting, 1)
        self.loop.create_task(coro())
        test_utils.run_briefly(self.loop)
        self.assertEqual(barrier.n_waiting, 2)

        t1.cancel()
        test_utils.run_briefly(self.loop)
        self.assertEqual(barrier.n_waiting, 1)
        self.loop.create_task(coro())
        test_utils.run_briefly(self.loop)
        self.assertEqual(barrier.n_waiting, 2)
        self.loop.create_task(coro())
        test_utils.run_briefly(self.loop)
        self.assertEqual(len(results), self.N)
        self.assertTrue(all(results))
        self.assertEqual(barrier.n_waiting, 0)
        self.assertFalse(barrier.broken)

    def test_wait_action_callback(self):
        result = []
        async def coro():
            ret = await barrier.wait()
            result.append(True)

        result1 = []
        self.N = 2
        barrier = asyncio.Barrier(self.N, action=lambda: result1.append(True))
        self.loop.create_task(coro())
        test_utils.run_briefly(self.loop)
        self.loop.create_task(coro())
        test_utils.run_briefly(self.loop)

        self.assertEqual(len(result1), 1)
        self.assertTrue(result1[0])
        self.assertEqual(len(result), 2)
        self.assertTrue(all(result))
        self.assertEqual(barrier.n_waiting, 0)
        self.assertFalse(barrier.broken)

    def test_wait_action_callback_more(self):
        result = []
        async def coro():
            ret = await barrier.wait()
            result.append(True)

        result1 = []

        self.N = 2
        more = 3
        barrier = asyncio.Barrier(self.N, action=lambda: result1.append(True))
        for _ in range(more):
            _ = [self.loop.create_task(coro()) for _ in range(self.N)]
            test_utils.run_briefly(self.loop)

        self.assertEqual(len(result1), more)
        self.assertTrue(all(result1))
        self.assertEqual(len(result), self.N*more)
        self.assertTrue(all(result))
        self.assertEqual(barrier.n_waiting, 0)
        self.assertFalse(barrier.broken)

    def test_wait_action_callback_error_broken(self):
        ERROR = ZeroDivisionError
        results1 = []
        results2 = []
        async def coro():
            try:
                ret = await barrier.wait()
            except ERROR:
                results1.append(False)
            except:
                results2.append(True)

        def raise_except():
            raise ERROR

        barrier = asyncio.Barrier(self.N, lambda: raise_except())
        _ = [self.loop.create_task(coro()) for _ in range(self.N)]
        test_utils.run_briefly(self.loop)
        self.assertEqual(len(results1), 1)
        self.assertFalse(results1[0])
        self.assertEqual(len(results2), self.N-1)
        self.assertTrue(all(results2))
        self.assertEqual(barrier.n_waiting, 0)

        self.assertTrue(barrier.broken)

    def test_reset(self):
        results1 = []
        results2 = []
        async def coro():
            try:
                await barrier.wait()
            except asyncio.BrokenBarrierError:
                results1.append(True)
            finally:
                await barrier.wait()
                results2.append(True)

        async def coro2():
            await barrier.wait()
            results2.append(True)


        barrier = asyncio.Barrier(self.N)
        _ = [self.loop.create_task(coro()) for _ in range(self.N-1)]
        test_utils.run_briefly(self.loop)
        barrier.reset()
        test_utils.run_briefly(self.loop)
        self.loop.create_task(coro2())
        test_utils.run_briefly(self.loop)
        self.assertFalse(barrier.broken)
        self.assertEqual(len(results1), self.N-1)
        self.assertEqual(len(results2), self.N)
        self.assertEqual(barrier.n_waiting, 0)

        self.assertFalse(barrier.broken)

    def test_reset_and_wait(self):
        results1 = []
        results2 = []
        results3 = []
        count = 0
        async def coro():
            nonlocal count

            i = await barrier1.wait()
            count += 1
            if count == self.N: # i == self.N//2:
                barrier.reset()
            else:
                try:
                    await barrier.wait()
                    results1.append(True)
                except Exception as e:
                    results2.append(True)

            # Now, pass the barrier again
            await barrier1.wait()
            results3.append(True)

        barrier = asyncio.Barrier(self.N)
        barrier1 = asyncio.Barrier(self.N)
        self.loop.run_until_complete(self.run_coros(self.N, coro))
        self.assertFalse(barrier.broken)
        self.assertEqual(len(results1), 0)
        self.assertEqual(len(results2), self.N-1)
        self.assertEqual(len(results3), self.N)
        self.assertEqual(barrier.n_waiting, 0)

        self.assertFalse(barrier.broken)

    def test_abort_broken(self):
        results1 = []
        results2 = []
        async def coro():
            try:
                i = await barrier.wait()
                if i == self.N//2:
                    raise RuntimeError
                await barrier.wait()
                results1.append(True)
            except asyncio.BrokenBarrierError:
                results2.append(True)
            except RuntimeError:
                barrier.abort()

        barrier = asyncio.Barrier(self.N)
        self.loop.run_until_complete(self.run_coros(self.N, coro))
        self.assertTrue(barrier.broken)
        self.assertEqual(len(results1), 0)
        self.assertEqual(len(results2), self.N-1)
        self.assertEqual(barrier.n_waiting, 0)

        self.assertTrue(barrier.broken)

    def test_abort_and_reset(self):
        results1 = []
        results2 = []
        results3 = []
        async def coro():
            try:
                i = await barrier.wait()
                if i == self.N//2:
                    raise RuntimeError
                await barrier.wait()
                results1.append(True)
            except asyncio.BrokenBarrierError:
                results2.append(True)
            except RuntimeError:
                barrier.abort()

            # Synchronize and reset the barrier.  Must synchronize first so
            # that everyone has left it when we reset, and after so that no
            # one enters it before the reset.
            i = await barrier2.wait()
            if  i == self.N//2:
                barrier.reset()
            await barrier2.wait()
            await barrier.wait()
            results3.append(True)

        barrier = asyncio.Barrier(self.N)
        barrier2 = asyncio.Barrier(self.N)
        self.loop.run_until_complete(self.run_coros(self.N, coro))
        self.assertFalse(barrier.broken)
        self.assertEqual(len(results1), 0)
        self.assertEqual(len(results2), self.N-1)
        self.assertEqual(len(results3), self.N)
        self.assertEqual(barrier.n_waiting, 0)

        self.assertFalse(barrier.broken)


if __name__ == '__main__':
    unittest.main()
