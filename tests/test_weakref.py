"""
Partial backport of Python 3.6's test.test_weakref:

    FinalizeTestCase

Backport modifications are marked with "XXX backport".
"""
from __future__ import print_function

import gc
import os
import platform

from backports import weakref

import unittest
from backports.test.support import script_helper


# Used by FinalizeTestCase as a global that may be replaced by None
# when the interpreter shuts down.
_global_var = 'foobar'


class FinalizeTestCase(unittest.TestCase):

    class A:
        pass

    def _collect_if_necessary(self):
        # we create no ref-cycles so in CPython no gc should be needed

        # XXX backport: Use platform.python_implementation instead of sys.implementation.name
        if platform.python_implementation().lower() != 'cpython':
            # XXX backport: Use gc.collect directly instead of test.support.gc_collect()
            gc.collect()
            # XXX backport: PyPy, at least, seems to require a second collection to pass.
            gc.collect()

    def test_finalize(self):
        def add(x,y,z):
            res.append(x + y + z)
            return x + y + z

        a = self.A()

        res = []
        f = weakref.finalize(a, add, 67, 43, z=89)
        self.assertEqual(f.alive, True)
        self.assertEqual(f.peek(), (a, add, (67,43), {'z':89}))
        self.assertEqual(f(), 199)
        self.assertEqual(f(), None)
        self.assertEqual(f(), None)
        self.assertEqual(f.peek(), None)
        self.assertEqual(f.detach(), None)
        self.assertEqual(f.alive, False)
        self.assertEqual(res, [199])

        res = []
        f = weakref.finalize(a, add, 67, 43, 89)
        self.assertEqual(f.peek(), (a, add, (67,43,89), {}))
        self.assertEqual(f.detach(), (a, add, (67,43,89), {}))
        self.assertEqual(f(), None)
        self.assertEqual(f(), None)
        self.assertEqual(f.peek(), None)
        self.assertEqual(f.detach(), None)
        self.assertEqual(f.alive, False)
        self.assertEqual(res, [])

        res = []
        f = weakref.finalize(a, add, x=67, y=43, z=89)
        del a
        self._collect_if_necessary()
        self.assertEqual(f(), None)
        self.assertEqual(f(), None)
        self.assertEqual(f.peek(), None)
        self.assertEqual(f.detach(), None)
        self.assertEqual(f.alive, False)
        self.assertEqual(res, [199])

    def test_order(self):
        a = self.A()
        res = []

        f1 = weakref.finalize(a, res.append, 'f1')
        f2 = weakref.finalize(a, res.append, 'f2')
        f3 = weakref.finalize(a, res.append, 'f3')
        f4 = weakref.finalize(a, res.append, 'f4')
        f5 = weakref.finalize(a, res.append, 'f5')

        # make sure finalizers can keep themselves alive
        del f1, f4

        self.assertTrue(f2.alive)
        self.assertTrue(f3.alive)
        self.assertTrue(f5.alive)

        self.assertTrue(f5.detach())
        self.assertFalse(f5.alive)

        f5()                       # nothing because previously unregistered
        res.append('A')
        f3()                       # => res.append('f3')
        self.assertFalse(f3.alive)
        res.append('B')
        f3()                       # nothing because previously called
        res.append('C')
        del a
        self._collect_if_necessary()
                                   # => res.append('f4')
                                   # => res.append('f2')
                                   # => res.append('f1')
        self.assertFalse(f2.alive)
        res.append('D')
        f2()                       # nothing because previously called by gc

        expected = ['A', 'f3', 'B', 'C', 'f4', 'f2', 'f1', 'D']
        self.assertEqual(res, expected)

    def test_all_freed(self):
        # we want a weakrefable subclass of weakref.finalize
        class MyFinalizer(weakref.finalize):
            pass

        a = self.A()
        res = []
        def callback():
            res.append(123)
        f = MyFinalizer(a, callback)

        wr_callback = weakref.ref(callback)
        wr_f = weakref.ref(f)
        del callback, f

        self.assertIsNotNone(wr_callback())
        self.assertIsNotNone(wr_f())

        del a
        self._collect_if_necessary()

        self.assertIsNone(wr_callback())
        self.assertIsNone(wr_f())
        self.assertEqual(res, [123])

    # TODO: Gather test coverage for this subprocess execution code.
    @classmethod
    def run_in_child(cls):  # pragma: no cover (executed in subprocess)
        def error():
            # Create an atexit finalizer from inside a finalizer called
            # at exit.  This should be the next to be run.
            g1 = weakref.finalize(cls, print, 'g1')
            print('f3 error')
            1/0

        # cls should stay alive till atexit callbacks run
        f1 = weakref.finalize(cls, print, 'f1', _global_var)
        f2 = weakref.finalize(cls, print, 'f2', _global_var)
        f3 = weakref.finalize(cls, error)
        f4 = weakref.finalize(cls, print, 'f4', _global_var)

        assert f1.atexit == True
        f2.atexit = False
        assert f3.atexit == True
        assert f4.atexit == True

    def test_atexit(self):
        # XXX backport: Adjust the import path to make this work in the subprocess.
        prog = ('from test_weakref import FinalizeTestCase;'+
                'FinalizeTestCase.run_in_child()')
        tests_dir = os.path.dirname(__file__)
        rc, out, err = script_helper.assert_python_ok('-c', prog, PYTHONPATH=tests_dir)

        out = out.decode('ascii').splitlines()
        self.assertEqual(out, ['f4 foobar', 'f3 error', 'g1', 'f1 foobar'])
        self.assertTrue(b'ZeroDivisionError' in err)
