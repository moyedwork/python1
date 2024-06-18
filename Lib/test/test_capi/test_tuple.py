import unittest
import sys
from collections import namedtuple
from test.support import import_helper

_testcapi = import_helper.import_module('_testcapi')
_testlimitedcapi = import_helper.import_module('_testlimitedcapi')

NULL = None
PY_SSIZE_T_MIN = _testcapi.PY_SSIZE_T_MIN
PY_SSIZE_T_MAX = _testcapi.PY_SSIZE_T_MAX

class TupleSubclass(tuple):
    pass


class CAPITest(unittest.TestCase):
    def test_check(self):
        # Test PyTuple_Check()
        check = _testlimitedcapi.tuple_check

        self.assertTrue(check((1, 2)))
        self.assertTrue(check(()))
        self.assertTrue(check(TupleSubclass((1, 2))))
        self.assertFalse(check({1: 2}))
        self.assertFalse(check([1, 2]))
        self.assertFalse(check(42))
        self.assertFalse(check(object()))

        # CRASHES check(NULL)

    def test_tuple_checkexact(self):
        # Test PyTuple_CheckExact()
        check = _testlimitedcapi.tuple_checkexact

        self.assertTrue(check((1, 2)))
        self.assertTrue(check(()))
        self.assertFalse(check(TupleSubclass((1, 2))))
        self.assertFalse(check({1: 2}))
        self.assertFalse(check([1, 2]))
        self.assertFalse(check(42))
        self.assertFalse(check(object()))

        # CRASHES check(NULL)

    def test_tuple_new(self):
        # Test PyTuple_New()
        tuple_new = _testlimitedcapi.tuple_new
        size = _testlimitedcapi.tuple_size
        checknull = _testcapi._check_item_is_NULL

        tup1 = tuple_new(0)
        self.assertEqual(tup1, ())
        self.assertEqual(size(tup1), 0)
        self.assertIs(type(tup1), tuple)
        tup2 = tuple_new(1)
        self.assertIs(type(tup2), tuple)
        self.assertEqual(size(tup2), 1)
        self.assertIsNot(tup2, tup1)
        self.assertTrue(checknull(tup2, 0))

        self.assertRaises(SystemError, tuple_new, -1)
        self.assertRaises(SystemError, tuple_new, PY_SSIZE_T_MIN)
        self.assertRaises(MemoryError, tuple_new, PY_SSIZE_T_MAX)

    def test_tuple_pack(self):
        # Test PyTuple_Pack()
        pack = _testlimitedcapi.tuple_pack

        self.assertEqual(pack(0), ())
        self.assertEqual(pack(1, 1), (1,))
        self.assertEqual(pack(2, 1, 2), (1, 2))
        self.assertEqual(pack(2, [1], 2), ([1], 2))

        self.assertRaises(SystemError, pack, PY_SSIZE_T_MIN)
        self.assertRaises(SystemError, pack, -1)
        self.assertRaises(MemoryError, pack, PY_SSIZE_T_MAX)

        # CRASHES pack(1, NULL)
        # CRASHES pack(2, 1)

    def test_tuple_size(self):
        # Test PyTuple_Size()
        size = _testlimitedcapi.tuple_size

        self.assertEqual(size((1, 2)), 2)
        self.assertEqual(size(TupleSubclass((1, 2))), 2)

        self.assertRaises(SystemError, size, [])
        self.assertRaises(SystemError, size, 42)
        self.assertRaises(SystemError, size, object())

        # CRASHES size(NULL)

    def test_tuple_get_size(self):
        # Test PyTuple_GET_SIZE()
        size = _testcapi.tuple_get_size

        self.assertEqual(size(()), 0)
        self.assertEqual(size((1, 2)), 2)
        self.assertEqual(size(TupleSubclass((1, 2))), 2)

    def test_tuple_getitem(self):
        # Test PyTuple_GetItem()
        getitem = _testlimitedcapi.tuple_getitem

        tup = TupleSubclass((1, 2, 3))
        self.assertEqual(getitem(tup, 0), 1)
        self.assertEqual(getitem(tup, 2), 3)

        tup = (1, [2], 3)
        self.assertEqual(getitem(tup, 0), 1)
        self.assertEqual(getitem(tup, 1), [2])
        self.assertEqual(getitem(tup, 2), 3)

        self.assertRaises(IndexError, getitem, tup, PY_SSIZE_T_MIN)
        self.assertRaises(IndexError, getitem, tup, -1)
        self.assertRaises(IndexError, getitem, tup, len(tup))
        self.assertRaises(IndexError, getitem, tup, PY_SSIZE_T_MAX)
        self.assertRaises(SystemError, getitem, [1, 2, 3], 1)
        self.assertRaises(SystemError, getitem, 42, 1)

        # CRASHES getitem(NULL, 1)

    def test_tuple_get_item(self):
        # Test PyTuple_GET_ITEM()
        get_item = _testcapi.tuple_get_item

        tup = TupleSubclass((1, 2, 3))
        self.assertEqual(get_item(tup, 0), 1)
        self.assertEqual(get_item(tup, 2), 3)

        tup = (1, [2], 3)
        self.assertEqual(get_item(tup, 0), 1)
        self.assertEqual(get_item(tup, 1), [2])
        self.assertEqual(get_item(tup, 2), 3)

    def test_tuple_getslice(self):
        # Test PyTuple_GetSlice()
        getslice = _testlimitedcapi.tuple_getslice

        # empty
        tup = (1, 2, 3)
        self.assertEqual(getslice(tup, PY_SSIZE_T_MIN, 0), ())
        self.assertEqual(getslice(tup, -1, 0), ())
        self.assertEqual(getslice(tup, 3, PY_SSIZE_T_MAX), ())
        self.assertEqual(getslice(tup, 0, 0), ())
        self.assertEqual(getslice(tup, 3, 0), ())
        tup = TupleSubclass((1, 2, 3))
        self.assertEqual(getslice(tup, PY_SSIZE_T_MIN, 0), ())
        self.assertEqual(getslice(tup, -1, 0), ())
        self.assertEqual(getslice(tup, 3, PY_SSIZE_T_MAX), ())
        self.assertEqual(getslice(tup, 0, 0), ())
        self.assertEqual(getslice(tup, 3, 0), ())

        # slice
        tup = (1, [2], 3)
        self.assertEqual(getslice(tup, 1, 3), ([2], 3))
        tup = TupleSubclass((1, [2], 3))
        self.assertEqual(getslice(tup, 1, 3), ([2], 3))

        # whole
        tup = (1, [2], 3)
        self.assertEqual(getslice(tup, 0, 3), tup)
        self.assertEqual(getslice(tup, 0, 100), tup)
        self.assertEqual(getslice(tup, -100, 100), tup)
        tup = TupleSubclass((1, [2], 3))
        self.assertEqual(getslice(tup, 0, 3), tup)
        self.assertEqual(getslice(tup, 0, 100), tup)
        self.assertEqual(getslice(tup, -100, 100), tup)

        self.assertRaises(SystemError, getslice, [1, [2], 3], 0, 1)
        self.assertRaises(SystemError, getslice, 42, 0, 1)

        # CRASHES getslice(NULL, 0, 0)

    def test_tuple_setitem(self):
        # Test PyTuple_SetItem()
        setitem = _testlimitedcapi.tuple_setitem
        checknull = _testcapi._check_item_is_NULL

        tup = (0, [0])
        self.assertEqual(setitem(tup, 0, [1]), ([1], [0]))
        self.assertEqual(setitem(tup, 1, [1]), (0, [1]))
        tup = setitem(tup, 1, NULL)
        self.assertTrue(checknull(tup, 1))

        self.assertRaises(IndexError, setitem, tup, PY_SSIZE_T_MIN, 1)
        self.assertRaises(IndexError, setitem, tup, -1, 1)
        self.assertRaises(IndexError, setitem, tup, len(tup), 1)
        self.assertRaises(IndexError, setitem, tup, PY_SSIZE_T_MAX, 1)
        self.assertRaises(SystemError, setitem, [1], 0, 1)
        self.assertRaises(SystemError, setitem, 42, 0, 1)

        # CRASHES setitem(NULL, 1, 5)

    def test_tuple_set_item(self):
        # Test PyTuple_SET_ITEM()
        set_item = _testcapi.tuple_set_item
        checknull = _testcapi._check_item_is_NULL

        tup = (0, [0])
        self.assertEqual(set_item(tup, 0, [1]), ([1], [0]))
        self.assertEqual(set_item(tup, 1, [1]), (0, [1]))
        tup = set_item(tup, 1, NULL)
        self.assertTrue(checknull(tup, 1))

    def test__tuple_resize(self):
        # Test _PyTuple_Resize()
        resize = _testcapi._tuple_resize
        checknull = _testcapi._check_item_is_NULL

        a = ()
        b = resize(a, 0)
        self.assertEqual(b, a)
        b = resize(a, 2)
        self.assertEqual(len(b), 2)

        a = (1, [2], [3])
        b = resize(a, 3)
        self.assertEqual(b, a)
        b = resize(a, 2)
        self.assertEqual(b, a[:2])
        b = resize(a, 5)
        self.assertEqual(len(b), 5)
        self.assertEqual(b[:3], a)
        self.assertTrue(all(checknull(b, i) for i in range(3, 5)))

        a = ()
        self.assertRaises(MemoryError, resize, a, PY_SSIZE_T_MAX)
        self.assertRaises(SystemError, resize, a, -1)
        self.assertRaises(SystemError, resize, a, PY_SSIZE_T_MIN)
        # refcount > 1
        a = (1, 2, 3)
        self.assertRaises(SystemError, resize, a, 2, False)
        # non-tuple
        a = [1, 2, 3]
        self.assertRaises(SystemError, resize, a, 2)


if __name__ == "__main__":
    unittest.main()
