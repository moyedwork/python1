from test.test_json import CTest
import test.support


class BadBool:
    def __bool__(self):
        1/0


class TestSpeedups(CTest):
    def test_scanstring(self):
        self.assertEqual(self.json.decoder.scanstring.__module__, "_json")
        self.assertIs(self.json.decoder.scanstring, self.json.decoder.c_scanstring)

    def test_encode_basestring_ascii(self):
        self.assertEqual(self.json.encoder.encode_basestring_ascii.__module__,
                         "_json")
        self.assertIs(self.json.encoder.encode_basestring_ascii,
                      self.json.encoder.c_encode_basestring_ascii)


class TestDecode(CTest):
    def test_make_scanner(self):
        self.assertRaises(AttributeError, self.json.scanner.c_make_scanner, 1)

    def test_bad_bool_args(self):
        def test(value):
            self.json.decoder.JSONDecoder(strict=BadBool()).decode(value)
        self.assertRaises(ZeroDivisionError, test, '""')
        self.assertRaises(ZeroDivisionError, test, '{}')


class TestEncode(CTest):
    def test_make_encoder(self):
        self.assertRaises(TypeError, self.json.encoder.c_make_encoder,
            (True, False),
            b"\xCD\x7D\x3D\x4E\x12\x4C\xF9\x79\xD7\x52\xBA\x82\xF2\x27\x4A\x7D\xA0\xCA\x75",
            None)

    @test.support.cpython_only
    def test_issue31505(self):
        # There shouldn't be an assertion failure in case c_make_encoder()
        # receives a bad encoder() argument.
        def _bad_encoder1(*args):
            return None
        enc = self.json.encoder.c_make_encoder(None, None, _bad_encoder1, None,
                                               'foo', 'bar', None, None, None)
        with self.assertRaises(TypeError):
            enc(obj='spam', _current_indent_level=4)
        with self.assertRaises(TypeError):
            enc(obj={'spam': 42}, _current_indent_level=4)

        def _bad_encoder2(*args):
            1/0
        enc = self.json.encoder.c_make_encoder(None, None, _bad_encoder2, None,
                                               'foo', 'bar', None, None, None)
        with self.assertRaises(ZeroDivisionError):
            enc(obj='spam', _current_indent_level=4)

    def test_bad_bool_args(self):
        def test(name):
            self.json.encoder.JSONEncoder(**{name: BadBool()}).encode({'a': 1})
        self.assertRaises(ZeroDivisionError, test, 'skipkeys')
        self.assertRaises(ZeroDivisionError, test, 'ensure_ascii')
        self.assertRaises(ZeroDivisionError, test, 'check_circular')
        self.assertRaises(ZeroDivisionError, test, 'allow_nan')
        self.assertRaises(ZeroDivisionError, test, 'sort_keys')

    def test_unsortable_keys(self):
        with self.assertRaises(TypeError):
            self.json.encoder.JSONEncoder(sort_keys=True).encode({'a': 1, 1: 'a'})
