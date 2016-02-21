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
Unit tests for `dbase32._dbase32py` module.
"""

from unittest import TestCase
from collections import Counter
import sys

from dbase32 import _dbase32py, gen

possible = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
assert ''.join(sorted(set(possible))) == possible
assert len(possible) == 36


class TestConstants(TestCase):
    def test_max(self):
        self.assertIsInstance(_dbase32py.MAX_BIN_LEN, int)
        self.assertIsInstance(_dbase32py.MAX_TXT_LEN, int)
        self.assertEqual(_dbase32py.MAX_BIN_LEN % 5, 0)
        self.assertEqual(_dbase32py.MAX_TXT_LEN % 8, 0)
        self.assertEqual(_dbase32py.MAX_BIN_LEN, _dbase32py.MAX_TXT_LEN * 5 // 8)

    def test_start(self):
        self.assertEqual(
            _dbase32py.DB32_START,
            ord(min(_dbase32py.DB32_FORWARD))
        )
        self.assertEqual(
            _dbase32py.DB32_START,
            ord(_dbase32py.DB32_FORWARD[0])
        )
        self.assertEqual(
            _dbase32py.DB32_START,
            gen.get_start(_dbase32py.DB32_FORWARD)
        )

    def test_end(self):
        self.assertEqual(
            _dbase32py.DB32_END,
            ord(max(_dbase32py.DB32_FORWARD))
        )
        self.assertEqual(
            _dbase32py.DB32_END,
            ord(_dbase32py.DB32_FORWARD[-1])
        )
        self.assertEqual(
            _dbase32py.DB32_END,
            gen.get_end(_dbase32py.DB32_FORWARD)
        )

    def test_forward(self):
        self.assertEqual(
            ''.join(sorted(set(_dbase32py.DB32_FORWARD))),
            _dbase32py.DB32_FORWARD
        )
        self.assertEqual(
            set(_dbase32py.DB32_FORWARD),
            set(possible) - set('012Z')
        )
        self.assertIsInstance(_dbase32py.DB32_FORWARD, str)
        self.assertEqual(len(_dbase32py.DB32_FORWARD), 32)
        self.assertEqual(_dbase32py.DB32_FORWARD, gen.gen_forward('012Z'))
        gen.check_forward(_dbase32py.DB32_FORWARD)

    def test_reverse(self):
        self.assertIsInstance(_dbase32py.DB32_REVERSE, tuple)
        self.assertEqual(len(_dbase32py.DB32_REVERSE), 256)
        self.assertEqual(min(_dbase32py.DB32_REVERSE), 0)
        self.assertEqual(max(_dbase32py.DB32_REVERSE), 255)
        self.assertEqual(
            _dbase32py.DB32_REVERSE,
            tuple(r.value for r in gen.gen_reverse(_dbase32py.DB32_FORWARD))
        )

        for (i, value) in enumerate(_dbase32py.DB32_REVERSE):
            if i < 51:
                self.assertEqual(value, 255)
            if 51 <= i <= 57:
                self.assertEqual(value, i - 51)
            if 58 <= i <= 64:
                self.assertEqual(value, 255)
            if 65 <= i <= 89:
                self.assertEqual(value, i - 58)
            if i > 89:
                self.assertEqual(value, 255)

        expected = set(range(32))
        expected.add(255)
        self.assertEqual(set(_dbase32py.DB32_REVERSE), expected)

        counts = Counter(_dbase32py.DB32_REVERSE)
        self.assertEqual(counts[255], 256 - 32)
        for i in range(32):
            self.assertEqual(counts[i], 1)

    def test_set(self):
        self.assertIsInstance(_dbase32py.DB32_SET, frozenset)
        self.assertEqual(_dbase32py.DB32_SET,
            frozenset(_dbase32py.DB32_FORWARD.encode('utf-8'))
        )


class TestFunctions(TestCase):
    def test_text_to_bytes(self):
        # Python >= 3.5 uses different buffer-related TypeError messages:
        if sys.version_info >= (3, 5):
            error1 = 'a bytes-like object is required, not {!r}'
            error2 = 'must be read-only bytes-like object, not bytearray'
        else:
            error1 = '{!r} does not support the buffer interface'
            error2 = 'must be read-only pinned buffer, not bytearray'

        with self.assertRaises(TypeError) as cm:
            _dbase32py._text_to_bytes(17)
        self.assertEqual(str(cm.exception), error1.format('int'))

        with self.assertRaises(TypeError) as cm:
            _dbase32py._text_to_bytes(18.5)
        self.assertEqual(str(cm.exception), error1.format('float'))

        with self.assertRaises(TypeError) as cm:
            _dbase32py._text_to_bytes(bytearray(b'3399AAYY'))
        self.assertEqual(str(cm.exception), error2)

        self.assertEqual(_dbase32py._text_to_bytes('3399AAYY'), b'3399AAYY')
        self.assertEqual(_dbase32py._text_to_bytes(b'3399AAYY'), b'3399AAYY')

        self.assertEqual(_dbase32py._text_to_bytes('four'), b'four')
        self.assertEqual(_dbase32py._text_to_bytes(b'four'), b'four')

    def test_check_length(self):
        # Test when len(text) is too small:
        with self.assertRaises(ValueError) as cm:
            _dbase32py._check_length(b'')
        self.assertEqual(
            str(cm.exception),
            'len(text) is 0, need 8 <= len(text) <= 96'
        )
        with self.assertRaises(ValueError) as cm:
            _dbase32py._check_length(b'-seven-')
        self.assertEqual(
            str(cm.exception),
            'len(text) is 7, need 8 <= len(text) <= 96'
        )

        # Test when len(text) is too big:
        with self.assertRaises(ValueError) as cm:
            _dbase32py._check_length(b'A' * 97)
        self.assertEqual(
            str(cm.exception),
            'len(text) is 97, need 8 <= len(text) <= 96'
        )

        # Test when len(text) % 8 != 0:
        with self.assertRaises(ValueError) as cm:
            _dbase32py._check_length(b'A' * 65)
        self.assertEqual(
            str(cm.exception),
            'len(text) is 65, need len(text) % 8 == 0'
        )

        text = b'12345678'
        self.assertIs(_dbase32py._check_length(text), text)

        text = b'Z' * 96
        self.assertIs(_dbase32py._check_length(text), text)

        text = b'R' * 24
        self.assertIs(_dbase32py._check_length(text), text)

        text = b'F' * 48
        self.assertIs(_dbase32py._check_length(text), text)

