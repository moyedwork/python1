from ctypes import Structure, c_char, c_uint32, c_ubyte, alignment, sizeof, Union
import inspect
import unittest


class TestAlignedStructures(unittest.TestCase):
    def test_aligned_string(self):
        data = bytearray(
            b'\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x68\x65\x6c\x6c\x6f\x20\x77\x6f\x72\x6c\x64\x21\x00\x00\x00\x00'
        )

        class Aligned(Structure):
            _align_ = 16
            _fields_ = [
                ('value', c_char * 16),
            ]

        class Main(Structure):
            _fields_ = [
                ('first', c_uint32),
                ('string', Aligned),
            ]

        main = Main.from_buffer(data)
        self.assertEqual(main.first, 7)
        self.assertEqual(main.string.value, b'hello world!')
        self.assertEqual(
            bytes(main.string.__buffer__(inspect.BufferFlags.SIMPLE)),
            b'\x68\x65\x6c\x6c\x6f\x20\x77\x6f\x72\x6c\x64\x21\x00\x00\x00\x00'
        )

    def test_aligned_structures(self):
        data = bytearray(
            b'\x01\x00\x01\x00\x07\x00\x00\x00'
        )

        class SomeBools(Structure):
            _align_ = 4
            _fields_ = [
                ("bool1", c_ubyte),
                ("bool2", c_ubyte),
                ("bool3", c_ubyte),
            ]
        class Main(Structure):
            _fields_ = [
                ("x", SomeBools),
                ("y", c_uint32),
            ]

        class SomeBoolsTooBig(Structure):
            _align_ = 8
            _fields_ = [
                ("bool1", c_ubyte),
                ("bool2", c_ubyte),
                ("bool3", c_ubyte),
            ]
        class MainTooBig(Structure):
            _fields_ = [
                ("x", SomeBoolsTooBig),
                ("y", c_uint32),
            ]
        main = Main.from_buffer(data)
        self.assertEqual(main.y, 7)
        self.assertEqual(alignment(SomeBools), 4)
        self.assertEqual(main.x.bool1, True)
        self.assertEqual(main.x.bool2, False)
        self.assertEqual(main.x.bool3, True)

        with self.assertRaises(ValueError) as ctx:
            MainTooBig.from_buffer(data)
            self.assertEqual(
                ctx.exception.args[0],
                'Buffer size too small (4 instead of at least 8 bytes)'
            )

    def test_aligned_subclasses(self):
        data = bytearray(
            b"\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00\x04\x00\x00\x00"
        )

        class UnalignedSub(Structure):
            x: c_uint32
            _fields_ = [
                ("x", c_uint32),
            ]

        class AlignedStruct(UnalignedSub):
            _align_ = 8
            y: c_uint32
            _fields_ = [
                ("y", c_uint32),
            ]

        class Main(Structure):
            _fields_ = [
                ("a", c_uint32),
                ("b", AlignedStruct)
            ]

        main = Main.from_buffer(data)
        self.assertEqual(alignment(main.b), 8)
        self.assertEqual(alignment(main), 8)
        self.assertEqual(sizeof(main.b), 8)
        self.assertEqual(sizeof(main), 16)
        self.assertEqual(main.a, 1)
        self.assertEqual(main.b.x, 3)
        self.assertEqual(main.b.y, 4)

    def test_aligned_union(self):
        data = bytearray(
            b"\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00\x04\x00\x00\x00"
        )

        class AlignedUnion(Union):
            _align_ = 8
            _fields_ = [
                ("a", c_uint32),
                ("b", c_ubyte * 8),
            ]

        class Main(Structure):
            _fields_ = [
                ("first", c_uint32),
                ("union", AlignedUnion),
            ]

        main = Main.from_buffer(data)
        self.assertEqual(main.first, 1)
        self.assertEqual(main.union.a, 3)
        self.assertEqual(bytes(main.union.b), b"\x03\x00\x00\x00\x04\x00\x00\x00")

    def test_aligned_struct_in_union(self):
        data = bytearray(
            b"\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00\x04\x00\x00\x00"
        )

        class Sub(Structure):
            _align_ = 8
            _fields_ = [
                ("x", c_uint32),
                ("y", c_uint32),
            ]

        class MainUnion(Union):
            _fields_ = [
                ("a", c_uint32),
                ("b", Sub),
            ]

        class Main(Structure):
            _fields_ = [
                ("first", c_uint32),
                ("union", MainUnion),
            ]

        main = Main.from_buffer(data)
        self.assertEqual(main.first, 1)
        self.assertEqual(main.union.a, 3)
        self.assertEqual(main.union.b.x, 3)
        self.assertEqual(main.union.b.y, 4)


if __name__ == '__main__':
    unittest.main()
