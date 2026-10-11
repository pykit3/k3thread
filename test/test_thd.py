import ctypes
import sys
import threading
import time
import unittest
from unittest import mock

import k3ut

import k3thread

dd = k3ut.dd


def _work(sess):
    try:
        # The exception is caught only after the worker has entered this try block.
        sess["started"].set()
        while True:
            _ = 1

    except SystemExit:
        sess["raised"] = True


class FakeSetAsyncExc:
    """
    Replaces PyThreadState_SetAsyncExc() and records its arguments as plain values.
    """

    def __init__(self, result):
        self.result = result
        self.calls = []

    def __call__(self, tid, exc):
        exc_type = None if exc is None else exc.value
        self.calls.append((tid.value, exc_type))
        return self.result


class TestThread(unittest.TestCase):
    def _verify_exception_raised(self, sess, thread):
        # we wait few seconds for the exception to be raised.
        for _ in range(100):
            if sess["raised"]:
                # The thread might still be alive at this point.
                time.sleep(0.2)
                self.assertFalse(thread.is_alive())
                break

            time.sleep(0.1)

        else:
            assert False, "SystemError is not raised"

    def test_send_exception(self):
        # send_exception does not work with PyPy
        if "PyPy" in sys.version:
            return

        sess = {"started": threading.Event(), "raised": False}

        t = k3thread.start(_work, args=(sess,), daemon=True)
        started = sess["started"].wait(10)
        self.assertTrue(started)
        self.assertFalse(sess["raised"])

        with self.assertRaises(TypeError):
            k3thread.send_exception("thread", SystemExit)

        with self.assertRaises(TypeError):
            k3thread.send_exception(t, SystemExit())

        class SomeClass:
            pass

        with self.assertRaises(ValueError):
            k3thread.send_exception(t, SomeClass)

        k3thread.send_exception(t, SystemExit)
        self._verify_exception_raised(sess, t)

    def test_send_exception_many_times(self):
        # send_exception does not work with PyPy
        if "PyPy" in sys.version:
            return

        sess = {"started": threading.Event(), "raised": False}

        t = k3thread.start(_work, args=(sess,), daemon=True)
        started = sess["started"].wait(10)
        self.assertTrue(started)
        self.assertFalse(sess["raised"])

        for _ in range(5):
            try:
                k3thread.send_exception(t, SystemExit)
            except k3thread.InvalidThreadIdError:
                # This will happen if the thread is already terminated by
                # a previous send_exception call.
                pass

        self._verify_exception_raised(sess, t)

        # Raising in a dead thread shoud not break.
        with self.assertRaises(k3thread.InvalidThreadIdError):
            k3thread.send_exception(t, SystemExit)

    def test_send_exception_not_alive(self):
        unstarted = threading.Thread(target=lambda: None)

        finished = k3thread.start(lambda: None)
        finished.join()

        for t in (unstarted, finished):
            with self.assertRaises(k3thread.InvalidThreadIdError):
                k3thread.send_exception(t, SystemExit)

    def test_send_exception_c_result(self):
        # send_exception does not work with PyPy
        if "PyPy" in sys.version:
            return

        # PyThreadState_SetAsyncExc() is replaced, so the thread receives no exception.
        stop = threading.Event()
        t = k3thread.start(stop.wait, daemon=True)

        # 0: no thread has this id.
        fake = FakeSetAsyncExc(0)
        with (
            mock.patch.object(ctypes.pythonapi, "PyThreadState_SetAsyncExc", fake),
            self.assertRaises(k3thread.InvalidThreadIdError) as ctx,
        ):
            k3thread.send_exception(t, SystemExit)

        self.assertEqual((t.ident,), ctx.exception.args)
        self.assertEqual([(t.ident, SystemExit)], fake.calls)

        # More than 1: several threads got the exception, so it is cleared again.
        fake = FakeSetAsyncExc(2)
        with (
            mock.patch.object(ctypes.pythonapi, "PyThreadState_SetAsyncExc", fake),
            self.assertRaises(k3thread.SendRaiseError) as ctx,
        ):
            k3thread.send_exception(t, SystemExit)

        self.assertIs(k3thread.SendRaiseError, type(ctx.exception))
        self.assertEqual(("PyThreadState_SetAsyncExc failed", 2), ctx.exception.args)
        self.assertEqual([(t.ident, SystemExit), (t.ident, None)], fake.calls)

        stop.set()
        t.join()

    def test_start(self):
        def _sort(a, reverse=False):
            a.sort(reverse=reverse)

        array = [3, 1, 2]
        t = k3thread.start(_sort, args=(array,))
        t.join()

        self.assertEqual(array, [1, 2, 3])

        t = k3thread.start(_sort, args=(array,), kwargs={"reverse": True})
        t.join()

        self.assertEqual(array, [3, 2, 1])

    def test_daemon(self):
        def noop():
            return None

        # Thread should be non-daemon by default
        t = k3thread.start(noop)
        self.assertFalse(t.daemon)

        t = k3thread.start(noop, daemon=True)
        self.assertTrue(t.daemon)

        t = k3thread.daemon(noop)
        self.assertTrue(t.daemon)

    def test_thread_after(self):
        def _do():
            pass

        with k3ut.Timer() as t:
            th = k3thread.start(target=_do, after=None)
            th.join()
            self.assertAlmostEqual(0, t.spent(), delta=0.1)

        with k3ut.Timer() as t:
            th = k3thread.start(target=_do, after=0.5)
            th.join()
            self.assertAlmostEqual(0.5, t.spent(), delta=0.1)

    def test_daemon_after(self):
        def _do():
            pass

        with k3ut.Timer() as t:
            th = k3thread.daemon(target=_do, after=None)
            th.join()
            self.assertAlmostEqual(0, t.spent(), delta=0.1)

        with k3ut.Timer() as t:
            th = k3thread.daemon(target=_do, after=0.5)
            th.join()
            self.assertAlmostEqual(0.5, t.spent(), delta=0.1)
