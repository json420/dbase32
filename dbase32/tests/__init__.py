# dbase32: base32-encoding with a sorted-order alphabet (for databases)
# Copyright (C) 2013-2016 Novacut Inc
#
# This file is part of `dbase32`.
#
# `dbase32` is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# `dbase32` is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with `dbase32`.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#   Jason Gerard DeRose <jderose@novacut.com>
#

"""
Unit tests for `dbase32` module.
"""

from unittest import TestCase
import sys
import os
from random import SystemRandom
import time
import base64
from collections import namedtuple

import dbase32
from dbase32 import _dbase32py

# True if the C extension is available
try:
    from dbase32 import _dbase32
    C_EXT_AVAIL = True
except ImportError:
    _dbase32 = None
    C_EXT_AVAIL = False


random = SystemRandom()

# Used in test_sort_p()
Tup = namedtuple('Tup', 'data b32 db32')

BIN_SIZES = (5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60)
TXT_SIZES = (8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96)
BAD_LETTERS = '\'"`~!#$%^&*()[]{}|+-_.,\/ 012:;<=>?@Zabcdefghijklmnopqrstuvwxyz'


def string_iter(index, count, a, b, c):
    assert 0 <= index < count
    for i in range(count):
        if i < index:
            yield a
        elif i == index:
            yield b
        else:
            yield c


def make_string(index, count, a, b, c=None):
    c = (a if c is None else c)
    return ''.join(string_iter(index, count, a, b, c))


def bytes_iter(ints):
    assert len(ints) % 8 == 0
    offset = 0
    taxi = 0
    for block in range(len(ints) // 8):
        for i in range(8):
            value = ints[offset + i]
            assert 0 <= value <= 31
            taxi = (taxi << 5) | value
        yield (taxi >> 32) & 255
        yield (taxi >> 24) & 255
        yield (taxi >> 16) & 255
        yield (taxi >>  8) & 255
        yield taxi & 255
        offset += 8


def make_bytes(ints):
    return bytes(bytes_iter(ints))


class TestConstants(TestCase):
    def skip_if_no_c_ext(self):
        if not C_EXT_AVAIL:
            self.skipTest('cannot import `dbase32._dbase32` C extension')

    def test_version(self):
        self.assertIsInstance(dbase32.__version__, str)
        (major, minor, micro) = dbase32.__version__.split('.')
        p1 = int(major)
        self.assertTrue(p1 >= 0)
        self.assertEqual(str(p1), major)
        p2 = int(minor)
        self.assertTrue(p2 >= 0)
        self.assertEqual(str(p2), minor)
        p3 = int(micro)
        self.assertTrue(p3 >= 0)
        self.assertEqual(str(p3), micro)

    def test_using_c_extension(self):
        self.assertIsInstance(dbase32.using_c_extension, bool)
        self.assertIn(dbase32.using_c_extension, (True, False))
        if C_EXT_AVAIL:
            self.assertIs(dbase32.using_c_extension, True)
        else:
            self.assertIs(dbase32.using_c_extension, False)

    def check_DB32ALPHABET(self, backend):
        self.assertIn(backend, (_dbase32, _dbase32py))
        value = backend.DB32ALPHABET
        self.assertIsInstance(value, str)
        self.assertEqual(len(value), 32)
        self.assertEqual(len(set(value)), 32)
        self.assertEqual(''.join(sorted(set(value))), value)
        self.assertEqual(value, _dbase32py.DB32ALPHABET)
        self.assertEqual(value, dbase32.DB32ALPHABET)
        return value

    def test_DB32ALPHABET_py(self):
        self.assertIs(
            self.check_DB32ALPHABET(_dbase32py),
            _dbase32py.DB32ALPHABET
        )
        if _dbase32 is None:
            self.assertIs(_dbase32py.DB32ALPHABET, dbase32.DB32ALPHABET)

    def test_DB32ALPHABET_c(self):
        self.skip_if_no_c_ext()
        self.assertIs(
            self.check_DB32ALPHABET(_dbase32),
            _dbase32.DB32ALPHABET
        )
        self.assertIs(_dbase32.DB32ALPHABET, dbase32.DB32ALPHABET)
        self.assertEqual(_dbase32.DB32ALPHABET, _dbase32py.DB32ALPHABET)

    def check_MAX_BIN_LEN(self, backend):
        self.assertIn(backend, (_dbase32, _dbase32py))
        value = backend.MAX_BIN_LEN
        self.assertEqual(value, dbase32.MAX_BIN_LEN)
        self.assertEqual(value, dbase32.MAX_TXT_LEN * 5 // 8)
        self.assertIsInstance(value, int)
        self.assertGreaterEqual(value, 5)
        self.assertEqual(value % 5, 0)
        self.assertLessEqual(value, 60)
        return value

    def test_MAX_BIN_LEN_py(self):
        self.assertIs(
            self.check_MAX_BIN_LEN(_dbase32py),
            _dbase32py.MAX_BIN_LEN
        )
        if _dbase32 is None:
            self.assertIs(_dbase32py.MAX_BIN_LEN, dbase32.MAX_BIN_LEN)

    def test_MAX_BIN_LEN_c(self):
        self.skip_if_no_c_ext()
        self.assertIs(
            self.check_MAX_BIN_LEN(_dbase32),
            _dbase32.MAX_BIN_LEN
        )
        self.assertIs(_dbase32.MAX_BIN_LEN, dbase32.MAX_BIN_LEN)
        self.assertEqual(_dbase32.MAX_BIN_LEN, _dbase32py.MAX_BIN_LEN)

    def check_MAX_TXT_LEN(self, backend):
        self.assertIn(backend, (_dbase32, _dbase32py))
        value = backend.MAX_TXT_LEN
        self.assertEqual(value, dbase32.MAX_TXT_LEN)
        self.assertEqual(value, dbase32.MAX_BIN_LEN * 8 // 5)
        self.assertIsInstance(value, int)
        self.assertGreaterEqual(value, 8)
        self.assertEqual(value % 8, 0)
        self.assertLessEqual(value, 96)
        return value

    def test_MAX_TXT_LEN_py(self):
        self.assertIs(
            self.check_MAX_TXT_LEN(_dbase32py),
            _dbase32py.MAX_TXT_LEN
        )
        if _dbase32 is None:
            self.assertIs(_dbase32py.MAX_TXT_LEN, dbase32.MAX_TXT_LEN)

    def test_MAX_TXT_LEN_c(self):
        self.skip_if_no_c_ext()
        self.assertIs(
            self.check_MAX_TXT_LEN(_dbase32),
            _dbase32.MAX_TXT_LEN
        )
        self.assertIs(_dbase32.MAX_TXT_LEN, dbase32.MAX_TXT_LEN)
        self.assertEqual(_dbase32.MAX_TXT_LEN, _dbase32py.MAX_TXT_LEN)

    def test_MAX_TXT_LEN(self):
        self.assertIsInstance(dbase32.MAX_TXT_LEN, int)
        self.assertEqual(dbase32.MAX_TXT_LEN, _dbase32py.MAX_TXT_LEN)

    def test_RANDOM_BITS(self):
        self.assertIsInstance(dbase32.RANDOM_BITS, int)
        self.assertEqual(dbase32.RANDOM_BITS % 40, 0)

    def test_RANDOM_BYTES(self):
        self.assertIsInstance(dbase32.RANDOM_BYTES, int)
        self.assertEqual(dbase32.RANDOM_BYTES, dbase32.RANDOM_BITS // 8)
        self.assertEqual(dbase32.RANDOM_BYTES % 5, 0)

    def test_RANDOM_B32LEN(self):
        self.assertIsInstance(dbase32.RANDOM_B32LEN, int)
        self.assertEqual(dbase32.RANDOM_B32LEN, dbase32.RANDOM_BITS // 5)
        self.assertEqual(dbase32.RANDOM_B32LEN % 8, 0)

    def test_MAX_BIN_LEN_alias(self):
        if C_EXT_AVAIL:
            self.assertIs(dbase32.MAX_BIN_LEN, _dbase32.MAX_BIN_LEN)
            self.assertEqual(dbase32.MAX_BIN_LEN, _dbase32py.MAX_BIN_LEN)
        else:
            self.assertIs(dbase32.MAX_BIN_LEN, _dbase32py.MAX_BIN_LEN)
            self.assertIsNone(_dbase32)

    def test_MAX_TXT_LEN_alias(self):
        if C_EXT_AVAIL:
            self.assertIs(dbase32.MAX_TXT_LEN, _dbase32.MAX_TXT_LEN)
            self.assertEqual(dbase32.MAX_TXT_LEN, _dbase32py.MAX_TXT_LEN)
        else:
            self.assertIs(dbase32.MAX_TXT_LEN, _dbase32py.MAX_TXT_LEN)
            self.assertIsNone(_dbase32)

    def test_DB32ALPHABET_alias(self):
        if C_EXT_AVAIL:
            self.assertIs(dbase32.DB32ALPHABET, _dbase32.DB32ALPHABET)
            self.assertEqual(dbase32.DB32ALPHABET, _dbase32py.DB32ALPHABET)
        else:
            self.assertIs(dbase32.DB32ALPHABET, _dbase32py.DB32ALPHABET)
            self.assertIsNone(_dbase32)

    def test_db32enc_alias(self):
        if C_EXT_AVAIL:
            self.assertIs(dbase32.db32enc, _dbase32.db32enc)
            self.assertIsNot(dbase32.db32enc, _dbase32py.db32enc)
        else:
            self.assertIs(dbase32.db32enc, _dbase32py.db32enc)

    def test_db32dec_alias(self):
        if C_EXT_AVAIL:
            self.assertIs(dbase32.db32dec, _dbase32.db32dec)
            self.assertIsNot(dbase32.db32dec, _dbase32py.db32dec)
        else:
            self.assertIs(dbase32.db32dec, _dbase32py.db32dec)

    def test_isdb32_alias(self):
        if C_EXT_AVAIL:
            self.assertIs(dbase32.isdb32, _dbase32.isdb32)
            self.assertIsNot(dbase32.isdb32, _dbase32py.isdb32)
        else:
            self.assertIs(dbase32.isdb32, _dbase32py.isdb32)

    def test_check_db32_alias(self):
        if C_EXT_AVAIL:
            self.assertIs(dbase32.check_db32, _dbase32.check_db32)
            self.assertIsNot(dbase32.check_db32, _dbase32py.check_db32)
        else:
            self.assertIs(dbase32.check_db32, _dbase32py.check_db32)

    def test_random_id_alias(self):
        if C_EXT_AVAIL:
            self.assertIs(dbase32.random_id, _dbase32.random_id)
            self.assertIsNot(dbase32.random_id, _dbase32py.random_id)
        else:
            self.assertIs(dbase32.random_id, _dbase32py.random_id)

    def test_time_id_alias(self):
        if C_EXT_AVAIL:
            self.assertIs(dbase32.time_id, _dbase32.time_id)
            self.assertIsNot(dbase32.time_id, _dbase32py.time_id)
        else:
            self.assertIs(dbase32.time_id, _dbase32py.time_id)

    def test_db32_relpath_alias(self):
        if C_EXT_AVAIL:
            self.assertIs(dbase32.db32_relpath, _dbase32.db32_relpath)
            self.assertIsNot(dbase32.db32_relpath, _dbase32py.db32_relpath)
        else:
            self.assertIs(dbase32.db32_relpath, _dbase32py.db32_relpath)

    def test_db32_abspath_alias(self):
        if C_EXT_AVAIL:
            self.assertIs(dbase32.db32_abspath, _dbase32.db32_abspath)
            self.assertIsNot(dbase32.db32_abspath, _dbase32py.db32_abspath)
        else:
            self.assertIs(dbase32.db32_abspath, _dbase32py.db32_abspath)

    def test_log_id_alias(self):
        self.assertIs(dbase32.log_id, dbase32.time_id)


class TestMisc(TestCase):
    def skip_if_no_c_ext(self):
        if not C_EXT_AVAIL:
            self.skipTest('cannot import `_dbase32` C extension')

    def test_make_string(self):
        self.assertEqual(make_string(0, 8, 'A', 'B'), 'BAAAAAAA')
        self.assertEqual(make_string(4, 8, 'A', 'B'), 'AAAABAAA')
        self.assertEqual(make_string(7, 8, 'A', 'B'), 'AAAAAAAB')
        self.assertEqual(make_string(0, 8, 'A', 'B', 'C'), 'BCCCCCCC')
        self.assertEqual(make_string(4, 8, 'A', 'B', 'C'), 'AAAABCCC')
        self.assertEqual(make_string(7, 8, 'A', 'B', 'C'), 'AAAAAAAB')

    def test_sort_p(self):
        """
        Confirm assumptions about RFC-3548 sort-order, test Dbase32 sort-order.
        """
        ids = [os.urandom(30) for i in range(1000)]
        ids.extend(os.urandom(15) for i in range(1500))

        orig = tuple(
            Tup(
                data,
                base64.b32encode(data).decode('utf-8'),
                _dbase32py.db32enc(data)
            )
            for data in ids
        )

        # Be really careful that we set things up correctly:
        for t in orig:
            self.assertIsInstance(t.data, bytes)
            self.assertIn(len(t.data), (30, 15))

            self.assertIsInstance(t.b32, str)
            self.assertIsInstance(t.db32, str)
            self.assertIn(len(t.b32), (24, 48))
            self.assertEqual(len(t.b32), len(t.db32))
            self.assertNotEqual(t.b32, t.db32)

            self.assertEqual(t.b32, base64.b32encode(t.data).decode('utf-8'))
            self.assertEqual(t.db32, _dbase32py.db32enc(t.data))

        # Now sort and compare:
        sort_by_data = sorted(orig, key=lambda t: t.data)
        sort_by_b32 = sorted(orig, key=lambda t: t.b32)
        sort_by_db32 = sorted(orig, key=lambda t: t.db32)
        self.assertNotEqual(sort_by_data, sort_by_b32)
        self.assertEqual(sort_by_data, sort_by_db32)

        # Extra safety that we didn't goof:
        sort_by_db32 = None
        sort_by_data.sort(key=lambda t: t.db32)  # Now sort by db32
        sort_by_b32.sort(key=lambda t: t.data)  # Now sort by data
        self.assertEqual(sort_by_data, sort_by_b32)

    def test_sort_c(self):
        """
        Test binary vs Dbase32 sort order, with a *lot* of values.
        """
        self.skip_if_no_c_ext()
        ids = [os.urandom(30) for i in range(20 * 1000)]
        ids.extend(os.urandom(15) for i in range(30 * 1000))
        pairs = tuple(
            (data, _dbase32.db32enc(data)) for data in ids
        )
        sort_by_bin = sorted(pairs, key=lambda t: t[0])
        sort_by_txt = sorted(pairs, key=lambda t: t[1])
        self.assertEqual(sort_by_bin, sort_by_txt)


class BackendTestCase(TestCase):
    """
    Base class for test cases for both Python and C implementations.
    """

    def setUp(self):
        backend = self.backend
        cls = self.__class__
        name = cls.__name__
        bases = cls.__bases__
        self.assertEqual(len(bases), 1)
        if name.endswith('_Py'):
            self.assertIs(backend, _dbase32py)
            self.assertIs(bases[0], BackendTestCase)
        elif name.endswith('_C'):
            self.assertIs(backend, _dbase32)
            self.assertIs(bases[0], TestFunctions_Py)
        else:
            raise Exception(
                'bad BackendTestCase subclass name: {!r}'.format(name)
            )
        if backend is None:
            self.skipTest('cannot import `dbase32._dbase32` C extension')

    def getattr(self, name):
        backend = self.backend
        self.assertIn(backend, (_dbase32py, _dbase32))
        self.assertIsNotNone(backend)
        if not hasattr(backend, name):
            raise Exception(
                '{!r} has no attribute {!r}'.format(backend.__name__, name)
            )
        return getattr(backend, name)

    def check_text_type(self, func, *args):
        """
        Common TypeError tests for `db32dec()`, `check_db32()`, and `isdb32()`.
        """

        # Python >= 3.5 uses different buffer-related TypeError messages:
        if sys.version_info >= (3, 5):
            error1 = 'a bytes-like object is required, not {!r}'
            error2 = 'must be read-only bytes-like object, not bytearray'
        else:
            error1 = '{!r} does not support the buffer interface'
            error2 = 'must be read-only pinned buffer, not bytearray'

        # Check that appropriate TypeError is raised:
        with self.assertRaises(TypeError) as cm:
            func(*(args + (17,)))
        self.assertEqual(str(cm.exception), error1.format('int'))
        with self.assertRaises(TypeError) as cm:
            func(*(args + (18.5,)))
        self.assertEqual(str(cm.exception), error1.format('float'))
        with self.assertRaises(TypeError) as cm:
            func(*(args + (bytearray(b'3399AAYY'),)))
        # FIXME: The Python 3.5.1 +whatever packages in Ubuntu Xenial have
        # recently changed this last message, not sure it's worth testing for
        # till things settle:
        if sys.version_info < (3, 5, 1):
            self.assertEqual(str(cm.exception), error2)

        # Sanity check to make sure both str and bytes can be decoded/validated:
        func(*(args + ('3399AAYY',)))
        func(*(args + (b'3399AAYY',)))

    def check_text_value(self, func, *args):
        """
        Common ValueError tests for `db32dec()` and `check_db32()`.
        """

        def mk_args(text):
            return args + (text,)

        # Test when len(text) is too small:
        with self.assertRaises(ValueError) as cm:
            func(*mk_args(''))
        self.assertEqual(
            str(cm.exception),
            'len(text) is 0, need 8 <= len(text) <= 96'
        )
        with self.assertRaises(ValueError) as cm:
            func(*mk_args('-seven-'))
        self.assertEqual(
            str(cm.exception),
            'len(text) is 7, need 8 <= len(text) <= 96'
        )

        # Test when len(text) is too big:
        with self.assertRaises(ValueError) as cm:
            func(*mk_args('A' * 97))
        self.assertEqual(
            str(cm.exception),
            'len(text) is 97, need 8 <= len(text) <= 96'
        )

        # Test when len(text) % 8 != 0:
        with self.assertRaises(ValueError) as cm:
            func(*mk_args('A' * 65))
        self.assertEqual(
            str(cm.exception),
            'len(text) is 65, need len(text) % 8 == 0'
        )

        # Test with invalid base32 characters:
        with self.assertRaises(ValueError) as cm:
            func(*mk_args('CDEFCDE2'))
        self.assertEqual(str(cm.exception), "invalid Dbase32: 'CDEFCDE2'")
        with self.assertRaises(ValueError) as cm:
            func(*mk_args('CDEFCDE='))
        self.assertEqual(str(cm.exception), "invalid Dbase32: 'CDEFCDE='")
        with self.assertRaises(ValueError) as cm:
            func(*mk_args('CDEFCDEZ'))
        self.assertEqual(str(cm.exception), "invalid Dbase32: 'CDEFCDEZ'")

        # Test that it stops at the first invalid letter:
        with self.assertRaises(ValueError) as cm:
            func(*mk_args('2ZZZZZZZ'))
        self.assertEqual(str(cm.exception), "invalid Dbase32: '2ZZZZZZZ'")
        with self.assertRaises(ValueError) as cm:
            func(*mk_args('AAAAAA=Z'))
        self.assertEqual(str(cm.exception), "invalid Dbase32: 'AAAAAA=Z'")
        with self.assertRaises(ValueError) as cm:
            func(*mk_args('CDEZ=2=2'))
        self.assertEqual(str(cm.exception), "invalid Dbase32: 'CDEZ=2=2'")

        # Test invalid letter at each possible position in the string
        for size in TXT_SIZES:
            for i in range(size):
                # Test when there is a single invalid letter:
                txt = make_string(i, size, 'A', '/')
                with self.assertRaises(ValueError) as cm:
                    func(*mk_args(txt))
                self.assertEqual(str(cm.exception),
                    'invalid Dbase32: {!r}'.format(txt)
                )
                txt = make_string(i, size, 'A', '.')
                with self.assertRaises(ValueError) as cm:
                    func(*mk_args(txt))
                self.assertEqual(str(cm.exception),
                    'invalid Dbase32: {!r}'.format(txt)
                )

                # Test that it stops at the *first* invalid letter:
                txt = make_string(i, size, 'A', '/', '.')
                with self.assertRaises(ValueError) as cm:
                    func(*mk_args(txt))
                self.assertEqual(str(cm.exception),
                    'invalid Dbase32: {!r}'.format(txt)
                )
                txt = make_string(i, size, 'A', '.', '/')
                with self.assertRaises(ValueError) as cm:
                    func(*mk_args(txt))
                self.assertEqual(str(cm.exception),
                    'invalid Dbase32: {!r}'.format(txt)
                )

        # Test a slew of no-no letters:
        for L in BAD_LETTERS:
            text = ('A' * 7) + L
            self.assertEqual(sys.getrefcount(text), 2)
            with self.assertRaises(ValueError) as cm:
                func(*mk_args(text))
            self.assertEqual(str(cm.exception),
                'invalid Dbase32: {!r}'.format(text)
            )
            self.assertEqual(sys.getrefcount(text), 2)
            data = text.encode()
            self.assertEqual(sys.getrefcount(data), 2)
            with self.assertRaises(ValueError) as cm:
                func(*mk_args(data))
            self.assertEqual(str(cm.exception),
                'invalid Dbase32: {!r}'.format(data)
            )
            self.assertEqual(sys.getrefcount(data), 2)

        # Test with multi-byte UTF-8 characters:
        bad_s = '™' * 8
        bad_b = bad_s.encode('utf-8')
        self.assertEqual(len(bad_s), 8)
        self.assertEqual(len(bad_b), 24)
        for value in [bad_s, bad_b]:
            refcount = sys.getrefcount(value)
            with self.assertRaises(ValueError) as cm:
                func(*mk_args(value))
            self.assertEqual(str(cm.exception),
                'invalid Dbase32: {!r}'.format(value)
            )
            self.assertEqual(sys.getrefcount(value), refcount)
        bad_s = 'AABBCCD™'
        bad_b = bad_s.encode('utf-8')
        self.assertEqual(len(bad_s), 8)
        self.assertEqual(len(bad_b), 10)
        for value in [bad_s, bad_b]:
            refcount = sys.getrefcount(value)
            with self.assertRaises(ValueError) as cm:
                func(*mk_args(value))
            self.assertEqual(
                str(cm.exception),
                'len(text) is 10, need len(text) % 8 == 0'
            )
            self.assertEqual(sys.getrefcount(value), refcount)
        bad_s = 'AABBC™'
        bad_b = bad_s.encode('utf-8')
        self.assertEqual(len(bad_s), 6)
        self.assertEqual(len(bad_b), 8)
        for value in [bad_s, bad_b]:
            refcount = sys.getrefcount(value)
            with self.assertRaises(ValueError) as cm:
                func(*mk_args(value))
            self.assertEqual(str(cm.exception),
                'invalid Dbase32: {!r}'.format(value)
            )
            self.assertEqual(sys.getrefcount(value), refcount)

        # Random bytes with invalid length:
        for size in TXT_SIZES:
            for offset in (-1, 1):
                badsize = size + offset
                bad = os.urandom(badsize)
                self.assertEqual(sys.getrefcount(bad), 2)
                with self.assertRaises(ValueError) as cm:
                    func(*mk_args(bad))
                if 8 <= badsize <= 96:
                    self.assertEqual(str(cm.exception),
                        'len(text) is {}, need len(text) % 8 == 0'.format(badsize)
                    )
                else:
                    self.assertEqual(str(cm.exception),
                        'len(text) is {}, need 8 <= len(text) <= 96'.format(badsize)
                    )
                self.assertEqual(sys.getrefcount(bad), 2)

        # Random bytes with invalid characeters:
        for size in TXT_SIZES:
            for i in range(100):
                bad = os.urandom(size)
                self.assertEqual(sys.getrefcount(bad), 2)
                with self.assertRaises(ValueError) as cm:
                    func(*mk_args(bad))
                self.assertEqual(str(cm.exception),
                    'invalid Dbase32: {!r}'.format(bad)
                )
                self.assertEqual(sys.getrefcount(bad), 2)


class TestFunctions_Py(BackendTestCase):
    """
    Unit tests for the pure-Python implementation.

    These tests should be run in full against the C implementation as well.
    """

    backend = _dbase32py

    def test_db32enc(self):
        db32enc = self.getattr('db32enc')

        # Test when len(data) is too small:
        with self.assertRaises(ValueError) as cm:
            db32enc(b'')
        self.assertEqual(
            str(cm.exception),
            'len(data) is 0, need 5 <= len(data) <= 60'
        )
        with self.assertRaises(ValueError) as cm:
            db32enc(b'four')
        self.assertEqual(
            str(cm.exception),
            'len(data) is 4, need 5 <= len(data) <= 60'
        )

        # Test when len(data) is too big:
        with self.assertRaises(ValueError) as cm:
            db32enc(b'B' * 61)
        self.assertEqual(
            str(cm.exception),
            'len(data) is 61, need 5 <= len(data) <= 60'
        )

        # Test when len(data) % 5 != 0:
        with self.assertRaises(ValueError) as cm:
            db32enc(b'B' * 41)
        self.assertEqual(
            str(cm.exception),
            'len(data) is 41, need len(data) % 5 == 0'
        )

        # Test a few handy static values:
        self.assertEqual(db32enc(b'\x00\x00\x00\x00\x00'), '33333333')
        self.assertEqual(db32enc(b'\xff\xff\xff\xff\xff'), 'YYYYYYYY')
        self.assertEqual(db32enc(b'\x00' * 60), '3' * 96)
        self.assertEqual(db32enc(b'\xff' * 60), 'Y' * 96)

        # Test all good symbols:
        int_list = list(range(32))
        self.assertEqual(
            db32enc(make_bytes(int_list)),
            '3456789ABCDEFGHIJKLMNOPQRSTUVWXY'
        )
        int_list.reverse()
        self.assertEqual(
            db32enc(make_bytes(int_list)),
            'YXWVUTSRQPONMLKJIHGFEDCBA9876543'
        )

        # Python >= 3.5 uses different buffer-related TypeError messages:
        if sys.version_info >= (3, 5):
            error = 'a bytes-like object is required, not {!r}'
        else:
            error = '{!r} does not support the buffer interface'

        # Test with wrong type:
        good = b'Bytes'
        self.assertEqual(db32enc(good), 'BCVQBSEM')
        for bad in [good.decode(), 17, 18.5]:
            with self.assertRaises(TypeError) as cm:
                db32enc(bad)
            self.assertEqual(
                str(cm.exception),
                error.format(type(bad).__name__)
            )

        # For override in TestFunctions_C:
        return db32enc

    def test_db32dec(self):
        db32dec = self.getattr('db32dec')

        # Common tests for text args:
        self.check_text_type(db32dec)
        self.check_text_value(db32dec)

        # Test a few handy static values:
        self.assertEqual(db32dec('33333333'), b'\x00\x00\x00\x00\x00')
        self.assertEqual(db32dec('YYYYYYYY'), b'\xff\xff\xff\xff\xff')
        self.assertEqual(db32dec('3' * 96), b'\x00' * 60)
        self.assertEqual(db32dec('Y' * 96), b'\xff' * 60)

        # For override in TestFunctions_C:
        return db32dec

    def test_db32enc_db32dec_roundtrip(self):
        """
        Test encode/decode round-trip between `db32enc()` and `db32dec()`.
        """
        db32enc = self.getattr('db32enc')
        db32dec = self.getattr('db32dec')

        for size in BIN_SIZES:
            for i in range(5000):
                data = os.urandom(size)
                text = db32enc(data)
                self.assertEqual(db32dec(text), data)
                self.assertEqual(db32dec(text.encode()), data)

    def test_isdb32(self):
        isdb32 = self.getattr('isdb32')

        # Common tests for text args (only check type in this case):
        self.check_text_type(isdb32)

        for size in TXT_SIZES:
            self.assertIs(isdb32('A' * (size - 1)), False)
            self.assertIs(isdb32('A' * (size + 1)), False)
            self.assertIs(isdb32('A' * size), True)
            self.assertIs(isdb32('Z' * size), False)

            self.assertIs(isdb32(b'A' * (size - 1)), False)
            self.assertIs(isdb32(b'A' * (size + 1)), False)
            self.assertIs(isdb32(b'A' * size), True)
            self.assertIs(isdb32(b'Z' * size), False)

            good = ''.join(
                random.choice(_dbase32py.DB32_FORWARD)
                for n in range(size)
            )
            self.assertIs(isdb32(good), True)
            self.assertIs(isdb32(good.encode('utf-8')), True)

            for L in BAD_LETTERS:
                bad = good[:-1] + L
                for value in [bad, bad.encode('utf-8')]:
                    self.assertEqual(len(value), size)
                    self.assertIs(isdb32(value), False)

            for i in range(size):
                bad = make_string(i, size, 'A', '/')
                for value in [bad, bad.encode('utf-8')]:
                    self.assertEqual(len(value), size)
                    self.assertIs(isdb32(value), False)
                g = make_string(i, size, 'A', 'B')
                self.assertIs(isdb32(g), True)
                self.assertIs(isdb32(g.encode('utf-8')), True)

            for i in range(size):
                for L in BAD_LETTERS:
                    bad = make_string(i, size, 'A', L)
                    for value in [bad, bad.encode('utf-8')]:
                        self.assertEqual(len(value), size)
                        self.assertIs(isdb32(value), False)

            # Multi-byte UTF-8 characters:
            bad_s = '™' * size
            bad_b = bad_s.encode('utf-8')
            self.assertEqual(len(bad_s), size)
            self.assertEqual(len(bad_b), size * 3)
            self.assertIs(isdb32(bad_s), False)
            self.assertIs(isdb32(bad_b), False)
            for i in range(size):
                bad_s = make_string(i, size, 'A', '™')
                bad_b = bad_s.encode('utf-8')
                self.assertEqual(len(bad_s), size)
                self.assertEqual(len(bad_b), size + 2)
                self.assertIs(isdb32(bad_s), False)
                self.assertIs(isdb32(bad_b), False)
            for i in range(size - 2):
                bad_s = make_string(i, size - 2, 'A', '™')
                bad_b = bad_s.encode('utf-8')
                self.assertEqual(len(bad_s), size - 2)
                self.assertEqual(len(bad_b), size)
                self.assertIs(isdb32(bad_s), False)
                self.assertIs(isdb32(bad_b), False)

    def test_check_db32(self):
        check_db32 = self.getattr('check_db32')

        # Common tests for text args:
        self.check_text_type(check_db32)
        self.check_text_value(check_db32)

        # Test a few handy static values:
        self.assertIsNone(check_db32('33333333'))
        self.assertIsNone(check_db32('YYYYYYYY'))
        self.assertIsNone(check_db32('3' * 96))
        self.assertIsNone(check_db32('Y' * 96))

        # Same, but bytes this time:
        self.assertIsNone(check_db32(b'33333333'))
        self.assertIsNone(check_db32(b'YYYYYYYY'))
        self.assertIsNone(check_db32(b'3' * 96))
        self.assertIsNone(check_db32(b'Y' * 96))

    def test_random_id(self):
        random_id = self.getattr('random_id')

        with self.assertRaises(TypeError) as cm:
            random_id(15.0)
        self.assertEqual(
            str(cm.exception),
            'integer argument expected, got float'
        )
        with self.assertRaises(TypeError) as cm:
            random_id('15')
        self.assertEqual(
            str(cm.exception),
            "'str' object cannot be interpreted as an integer"
        )

        with self.assertRaises(ValueError) as cm:
            random_id(4)
        self.assertEqual(
            str(cm.exception),
            'numbytes is 4, need 5 <= numbytes <= 60'
        )
        with self.assertRaises(ValueError) as cm:
            random_id(29)
        self.assertEqual(
            str(cm.exception),
            'numbytes is 29, need numbytes % 5 == 0'
        )

        _id = random_id()
        self.assertIsInstance(_id, str)
        self.assertEqual(len(_id), dbase32.RANDOM_B32LEN)
        data = dbase32.db32dec(_id)
        self.assertIsInstance(data, bytes)
        self.assertEqual(len(data), dbase32.RANDOM_BYTES)
        self.assertEqual(dbase32.db32enc(data), _id)

        _id = random_id(dbase32.RANDOM_BYTES)
        self.assertIsInstance(_id, str)
        self.assertEqual(len(_id), dbase32.RANDOM_B32LEN)
        data = dbase32.db32dec(_id)
        self.assertIsInstance(data, bytes)
        self.assertEqual(len(data), dbase32.RANDOM_BYTES)
        self.assertEqual(dbase32.db32enc(data), _id)

        _id = random_id(numbytes=dbase32.RANDOM_BYTES)
        self.assertIsInstance(_id, str)
        self.assertEqual(len(_id), dbase32.RANDOM_B32LEN)
        data = dbase32.db32dec(_id)
        self.assertIsInstance(data, bytes)
        self.assertEqual(len(data), dbase32.RANDOM_BYTES)
        self.assertEqual(dbase32.db32enc(data), _id)

        for size in BIN_SIZES:
            _id = random_id(size)
            self.assertIsInstance(_id, str)
            self.assertEqual(len(_id), size * 8 // 5)
            data = dbase32.db32dec(_id)
            self.assertIsInstance(data, bytes)
            self.assertEqual(len(data), size)
            self.assertEqual(dbase32.db32enc(data), _id)

        # Sanity check on their randomness:
        count = 25000
        accum = set(random_id() for i in range(count))
        self.assertEqual(len(accum), count)

        # Type check on numbytes:
        with self.assertRaises(TypeError) as cm:
            random_id([])
        if self.backend is _dbase32py:
            msg = "numbytes must be an int; got <class 'list'>"
        else:
            msg = "'list' object cannot be interpreted as an integer"
        self.assertEqual(str(cm.exception), msg)

        # FIXME: test with float too, possibly sync up error message from
        # Python and C implementations

    def test_time_id(self):
        time_id = self.getattr('time_id')

        def ts_bin(timestamp):
            assert isinstance(timestamp, (int, float))
            ts = int(timestamp)
            assert ts >= 0
            buf = bytearray()
            buf.append((ts >> 24) & 255)
            buf.append((ts >> 16) & 255)
            buf.append((ts >>  8) & 255)
            buf.append(ts & 255)
            return bytes(buf)

        accum = set()
        for n in range(250):
            # Don't provide timestamp:
            start = int(time.time())
            _id = time_id()
            end = int(time.time())
            self.assertIsInstance(_id, str)
            self.assertEqual(len(_id), 24)
            self.assertTrue(set(_id).issubset(_dbase32py.DB32_FORWARD))
            possible = set(ts_bin(i) for i in range(start - 1, end + 2))
            data = _dbase32py.db32dec(_id)
            self.assertIn(data[:4], possible)
            accum.add(data[4:])

            # Current timestamp:
            timestamp = time.time()
            _id = time_id(timestamp)
            self.assertIsInstance(_id, str)
            self.assertEqual(len(_id), 24)
            self.assertTrue(set(_id).issubset(_dbase32py.DB32_FORWARD))
            data = _dbase32py.db32dec(_id)
            self.assertEqual(data[:4], ts_bin(timestamp))
            accum.add(data[4:])

            # Smallest timestamp:
            _id = time_id(0)
            self.assertIsInstance(_id, str)
            self.assertEqual(len(_id), 24)
            self.assertTrue(set(_id).issubset(_dbase32py.DB32_FORWARD))
            data = _dbase32py.db32dec(_id)
            self.assertEqual(data[:4], bytes([0, 0, 0, 0]))
            accum.add(data[4:])

            # Largest timestamp:
            _id = time_id(2**32 - 1)
            self.assertIsInstance(_id, str)
            self.assertEqual(len(_id), 24)
            self.assertTrue(set(_id).issubset(_dbase32py.DB32_FORWARD))
            data = _dbase32py.db32dec(_id)
            self.assertEqual(data[:4], bytes([255, 255, 255, 255]))
            accum.add(data[4:])

        # Make sure final 80 bits are actually random:
        self.assertEqual(len(accum), 1000)

    def test_db32_relpath(self):
        db32_relpath = self.getattr('db32_relpath')

        # Common tests for text args:
        self.check_text_type(db32_relpath)
        self.check_text_value(db32_relpath)

        # Sanity check with a few static values:
        self.assertEqual(db32_relpath('AABBBBBB'), 'AA/BBBBBB')
        self.assertEqual(db32_relpath('AABBBBBBCCCCCCCC'), 'AA/BBBBBBCCCCCCCC')

        # Use fastest random_id() implementation regardless of backend:
        fastest = (_dbase32 if C_EXT_AVAIL else _dbase32py)
        random_id = fastest.random_id

        # Test with random values:
        for size in BIN_SIZES:
            length = (size * 8 // 5) + 1
            for i in range(1000):
                text = random_id(size)
                for arg in (text, text.encode()):  # Test both str and bytes
                    rp = db32_relpath(arg)
                    self.assertIs(type(rp), str)
                    self.assertEqual(len(rp), length)
                    self.assertEqual(rp[2], '/')
                    self.assertEqual(rp, '/'.join([text[:2], text[2:]]))

    def test_db32_abspath(self):
        db32_abspath = self.getattr('db32_abspath')
        db32_relpath = self.getattr('db32_relpath')

        # Use fastest random_id() implementation regardless of backend:
        fastest = (_dbase32 if C_EXT_AVAIL else _dbase32py)
        random_id = fastest.random_id
        parentdir = '/'.join(['/tmp', random_id(), random_id()])

        # Common tests for text args:
        self.check_text_type(db32_abspath, parentdir)
        self.check_text_value(db32_abspath, parentdir)

        # Sanity check with a few static values:
        self.assertEqual(db32_abspath('/PP', 'AABBBBBB'), '/PP/AA/BBBBBB')
        self.assertEqual(
            db32_abspath('/PP', 'AABBBBBBCCCCCCCC'),
            '/PP/AA/BBBBBBCCCCCCCC'
        )

        # Test with random values:
        for size in BIN_SIZES:
            length = len(parentdir) + (size * 8 // 5) + 2
            for i in range(1000):
                text = random_id(size)
                rp = db32_relpath(text)
                expected = '/'.join([parentdir, rp])
                for arg in (text, text.encode()):  # Test both str and bytes
                    p = db32_abspath(parentdir, text)
                    self.assertIs(type(p), str)
                    self.assertEqual(len(p), length)
                    self.assertEqual(p, expected)


class TestFunctions_C(TestFunctions_Py):
    """
    Unit tests for the C implementation.

    If overrides are needed, these tests should run the full Python
    implementation test by calling the super() method of the same name, plus
    then run any additional C-specific tests.
    """

    backend = _dbase32

    def test_db32enc(self):
        db32enc = super().test_db32enc()
        self.assertIs(db32enc, _dbase32.db32enc)
        py_db32enc = _dbase32py.db32enc
        self.assertIsNot(db32enc, py_db32enc)

        # Compare against the Python version of db32enc:
        for size in BIN_SIZES:
            for i in range(5000):
                data = os.urandom(size)
                self.assertEqual(db32enc(data), py_db32enc(data))

    def test_db32dec(self):
        db32dec = super().test_db32dec()
        self.assertIs(db32dec, _dbase32.db32dec)
        py_db32dec = _dbase32py.db32dec
        self.assertIsNot(db32dec, py_db32dec)
        DB32_FORWARD = _dbase32py.DB32_FORWARD

        # Compare against the Python version db32dec:
        for size in TXT_SIZES:
            for i in range(1000):
                text_s = ''.join(
                    random.choice(DB32_FORWARD)
                    for n in range(size)
                )
                text_b = text_s.encode('utf-8')
                self.assertEqual(len(text_s), size)
                self.assertEqual(len(text_b), size)
                data = py_db32dec(text_s)
                self.assertEqual(len(data), size * 5 // 8)
                self.assertEqual(py_db32dec(text_b), data)
                self.assertEqual(db32dec(text_s), data)
                self.assertEqual(db32dec(text_b), data)

