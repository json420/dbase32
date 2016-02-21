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
Unit tests for `dbase32.rfc3548` module.

This validates the underlying `encode_x()`, `decode_x()` functions against the
`base64.b32encode()`, `base64.b32decode()` functions in the Python standard
library.
"""

from unittest import TestCase
import os
import base64
from random import SystemRandom
from collections import Counter
import sys

from dbase32 import rfc3548, gen


random = SystemRandom()

BIN_SIZES = (5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60)
TXT_SIZES = (8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96)

BAD_LETTERS = '\'"`~!#$%^&*()[]{}|+-_.,\/ 0189:;<=>?@abcdefghijklmnopqrstuvwxyz'


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


class TestConstants(TestCase):
    def test_start(self):
        self.assertEqual(
            rfc3548.B32_START,
            ord(min(rfc3548.B32_FORWARD))
        )
        self.assertEqual(
            rfc3548.B32_START,
            ord(rfc3548.B32_FORWARD[26])
        )

    def test_end(self):
        self.assertEqual(
            rfc3548.B32_END,
            ord(max(rfc3548.B32_FORWARD))
        )
        self.assertEqual(
            rfc3548.B32_END,
            ord(rfc3548.B32_FORWARD[25])
        )

    def test_forward(self):
        self.assertIsInstance(rfc3548.B32_FORWARD, str)
        self.assertEqual(len(rfc3548.B32_FORWARD), 32)
        sb32 = gen.gen_forward('0189')
        self.assertEqual(set(rfc3548.B32_FORWARD), set(sb32))
        self.assertNotEqual(rfc3548.B32_FORWARD, sb32)

    def test_reverse(self):
        self.assertIsInstance(rfc3548.B32_REVERSE, tuple)
        self.assertEqual(len(rfc3548.B32_REVERSE), 256)
        self.assertEqual(min(rfc3548.B32_REVERSE), 0)
        self.assertEqual(max(rfc3548.B32_REVERSE), 255)
        self.assertEqual(
            rfc3548.B32_REVERSE,
            tuple(r.value for r in gen.gen_reverse(rfc3548.B32_FORWARD))
        )

        for (i, value) in enumerate(rfc3548.B32_REVERSE):
            if i < 50:
                self.assertEqual(value, 255)
            if 50 <= i <= 55:
                self.assertEqual(value, i - 24)
            if 56 <= i <= 64:
                self.assertEqual(value, 255)
            if 65 <= i <= 90:
                self.assertEqual(value, i - 65)
            if i > 90:
                self.assertEqual(value, 255)

        expected = set(range(32))
        expected.add(255)
        self.assertEqual(set(rfc3548.B32_REVERSE), expected)

        counts = Counter(rfc3548.B32_REVERSE)
        self.assertEqual(counts[255], 256 - 32)
        for i in range(32):
            self.assertEqual(counts[i], 1)

    def test_set(self):
        self.assertIsInstance(rfc3548.B32_SET, frozenset)
        self.assertEqual(rfc3548.B32_SET,
            frozenset(rfc3548.B32_FORWARD.encode('utf-8'))
        )


class TestFunctions(TestCase):
    def check_text_type(self, func):
        """
        Common TypeError tests for `b32dec()`, `check_b32()`, and `isb32()`.
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
            func(17)
        self.assertEqual(str(cm.exception), error1.format('int'))
        with self.assertRaises(TypeError) as cm:
            func(18.5)
        self.assertEqual(str(cm.exception), error1.format('float'))
        with self.assertRaises(TypeError) as cm:
            func(bytearray(b'3399AAYY'))
        self.assertEqual(str(cm.exception), error2)

        # Sanity check to make sure both str and bytes can be decoded/validated:
        func('AAZZ2277')
        func(b'AAZZ2277')

    def check_text_value(self, func):
        """
        Common ValueError tests for `b32dec()` and `check_b32()`.
        """
        # Test when len(text) is too small:
        with self.assertRaises(ValueError) as cm:
            func('')
        self.assertEqual(
            str(cm.exception),
            'len(text) is 0, need 8 <= len(text) <= 96'
        )
        with self.assertRaises(ValueError) as cm:
            func('-seven-')
        self.assertEqual(
            str(cm.exception),
            'len(text) is 7, need 8 <= len(text) <= 96'
        )

        # Test when len(text) is too big:
        with self.assertRaises(ValueError) as cm:
            func('A' * 97)
        self.assertEqual(
            str(cm.exception),
            'len(text) is 97, need 8 <= len(text) <= 96'
        )

        # Test when len(text) % 8 != 0:
        with self.assertRaises(ValueError) as cm:
            func('A' * 65)
        self.assertEqual(
            str(cm.exception),
            'len(text) is 65, need len(text) % 8 == 0'
        )

        # Test with invalid base32 characters:
        with self.assertRaises(ValueError) as cm:
            func('CDEFCDE8')
        self.assertEqual(str(cm.exception), "invalid Dbase32: 'CDEFCDE8'")
        with self.assertRaises(ValueError) as cm:
            func('CDEFCDE=')
        self.assertEqual(str(cm.exception), "invalid Dbase32: 'CDEFCDE='")
        with self.assertRaises(ValueError) as cm:
            func('CDEFCDE9')
        self.assertEqual(str(cm.exception), "invalid Dbase32: 'CDEFCDE9'")

        # Test that it stops at the first invalid letter:
        with self.assertRaises(ValueError) as cm:
            func('89999999')
        self.assertEqual(str(cm.exception), "invalid Dbase32: '89999999'")
        with self.assertRaises(ValueError) as cm:
            func('AAAAAA=0')
        self.assertEqual(str(cm.exception), "invalid Dbase32: 'AAAAAA=0'")
        with self.assertRaises(ValueError) as cm:
            func('CDE8=0=0')
        self.assertEqual(str(cm.exception), "invalid Dbase32: 'CDE8=0=0'")

        # Test invalid letter at each possible position in the string
        for size in TXT_SIZES:
            for i in range(size):
                # Test when there is a single invalid letter:
                txt = make_string(i, size, 'A', '/')
                with self.assertRaises(ValueError) as cm:
                    func(txt)
                self.assertEqual(str(cm.exception),
                    'invalid Dbase32: {!r}'.format(txt)
                )
                txt = make_string(i, size, 'A', '.')
                with self.assertRaises(ValueError) as cm:
                    func(txt)
                self.assertEqual(str(cm.exception),
                    'invalid Dbase32: {!r}'.format(txt)
                )

                # Test that it stops at the *first* invalid letter:
                txt = make_string(i, size, 'A', '/', '.')
                with self.assertRaises(ValueError) as cm:
                    func(txt)
                self.assertEqual(str(cm.exception),
                    'invalid Dbase32: {!r}'.format(txt)
                )
                txt = make_string(i, size, 'A', '.', '/')
                with self.assertRaises(ValueError) as cm:
                    func(txt)
                self.assertEqual(str(cm.exception),
                    'invalid Dbase32: {!r}'.format(txt)
                )

        # Test a slew of no-no letters:
        for L in BAD_LETTERS:
            txt = ('A' * 7) + L
            with self.assertRaises(ValueError) as cm:
                func(txt)
            self.assertEqual(str(cm.exception),
                'invalid Dbase32: {!r}'.format(txt)
            )

        # Test with multi-byte UTF-8 characters:
        bad_s = '™' * 8
        bad_b = bad_s.encode('utf-8')
        self.assertEqual(len(bad_s), 8)
        self.assertEqual(len(bad_b), 24)
        for value in [bad_s, bad_b]:
            with self.assertRaises(ValueError) as cm:
                func(value)
            self.assertEqual(str(cm.exception),
                'invalid Dbase32: {!r}'.format(value)
            )
        bad_s = 'AABBCCD™'
        bad_b = bad_s.encode('utf-8')
        self.assertEqual(len(bad_s), 8)
        self.assertEqual(len(bad_b), 10)
        for value in [bad_s, bad_b]:
            with self.assertRaises(ValueError) as cm:
                func(value)
            self.assertEqual(
                str(cm.exception),
                'len(text) is 10, need len(text) % 8 == 0'
            )
        bad_s = 'AABBC™'
        bad_b = bad_s.encode('utf-8')
        self.assertEqual(len(bad_s), 6)
        self.assertEqual(len(bad_b), 8)
        for value in [bad_s, bad_b]:
            with self.assertRaises(ValueError) as cm:
                func(value)
            self.assertEqual(str(cm.exception),
                'invalid Dbase32: {!r}'.format(value)
            )

    def test_b32enc(self):
        """
        Test `dbase32.encode_x()` against `base64.b32encode()`.
        """
        # A few static value sanity checks:
        self.assertEqual(rfc3548.b32enc(b'\x00\x00\x00\x00\x00'), 'AAAAAAAA')
        self.assertEqual(rfc3548.b32enc(b'\xff\xff\xff\xff\xff'), '77777777')
        self.assertEqual(rfc3548.b32enc(b'\x00' * 60), 'A' * 96)
        self.assertEqual(rfc3548.b32enc(b'\xff' * 60), '7' * 96)

        # Compare against base64.b32encode() from stdlib:
        for size in BIN_SIZES:
            for i in range(100):
                data = os.urandom(size)
                self.assertEqual(
                    rfc3548.b32enc(data),
                    base64.b32encode(data).decode('utf-8')
                )

    def test_b32dec(self):
        """
        Test `dbase32.decode_x()` against `base64.b32decode()`.
        """
        self.check_text_type(rfc3548.b32dec)
        self.check_text_value(rfc3548.b32dec)

        # A few static value sanity checks:
        self.assertEqual(rfc3548.b32dec('AAAAAAAA'), b'\x00\x00\x00\x00\x00')
        self.assertEqual(rfc3548.b32dec('77777777'), b'\xff\xff\xff\xff\xff')
        self.assertEqual(rfc3548.b32dec('A' * 96), b'\x00' * 60)
        self.assertEqual(rfc3548.b32dec('7' * 96), b'\xff' * 60)

        # Compare against base64.b32decode() from stdlib:
        for size in TXT_SIZES:
            for i in range(100):
                text_s = ''.join(
                    random.choice(rfc3548.B32_FORWARD) for n in range(size)
                )
                text_b = text_s.encode('utf-8')
                self.assertEqual(len(text_s), size)
                self.assertEqual(len(text_b), size)
                data = base64.b32decode(text_b)
                self.assertEqual(len(data), size * 5 // 8)
                self.assertEqual(rfc3548.b32dec(text_s), data)
                self.assertEqual(rfc3548.b32dec(text_b), data)

    def test_check_b32(self):
        self.check_text_type(rfc3548.check_b32)
        self.check_text_value(rfc3548.check_b32)

        # Test a few handy static values:
        self.assertIsNone(rfc3548.check_b32('22222222'))
        self.assertIsNone(rfc3548.check_b32('ZZZZZZZZ'))
        self.assertIsNone(rfc3548.check_b32('2' * 96))
        self.assertIsNone(rfc3548.check_b32('Z' * 96))

        # Same, but bytes this time:
        self.assertIsNone(rfc3548.check_b32(b'22222222'))
        self.assertIsNone(rfc3548.check_b32(b'ZZZZZZZZ'))
        self.assertIsNone(rfc3548.check_b32(b'2' * 96))
        self.assertIsNone(rfc3548.check_b32(b'Z' * 96))

    def test_isb32(self):
        self.check_text_type(rfc3548.isb32)
        for size in TXT_SIZES:
            self.assertIs(rfc3548.isb32('A' * (size - 1)), False)
            self.assertIs(rfc3548.isb32('A' * (size + 1)), False)
            self.assertIs(rfc3548.isb32('A' * size), True)
            self.assertIs(rfc3548.isb32('8' * size), False)

            self.assertIs(rfc3548.isb32(b'A' * (size - 1)), False)
            self.assertIs(rfc3548.isb32(b'A' * (size + 1)), False)
            self.assertIs(rfc3548.isb32(b'A' * size), True)
            self.assertIs(rfc3548.isb32(b'8' * size), False)

            good = ''.join(
                random.choice(rfc3548.B32_FORWARD)
                for n in range(size)
            )
            self.assertIs(rfc3548.isb32(good), True)
            self.assertIs(rfc3548.isb32(good.encode('utf-8')), True)

            for L in BAD_LETTERS:
                bad = good[:-1] + L
                for value in [bad, bad.encode('utf-8')]:
                    self.assertEqual(len(value), size)
                    self.assertIs(rfc3548.isb32(value), False)

            for i in range(size):
                bad = make_string(i, size, 'A', '/')
                for value in [bad, bad.encode('utf-8')]:
                    self.assertEqual(len(value), size)
                    self.assertIs(rfc3548.isb32(value), False)
                g = make_string(i, size, 'A', 'B')
                self.assertIs(rfc3548.isb32(g), True)
                self.assertIs(rfc3548.isb32(g.encode('utf-8')), True)

            for i in range(size):
                for L in BAD_LETTERS:
                    bad = make_string(i, size, 'A', L)
                    for value in [bad, bad.encode('utf-8')]:
                        self.assertEqual(len(value), size)
                        self.assertIs(rfc3548.isb32(value), False)

            # Multi-byte UTF-8 characters:
            bad_s = '™' * size
            bad_b = bad_s.encode('utf-8')
            self.assertEqual(len(bad_s), size)
            self.assertEqual(len(bad_b), size * 3)
            self.assertIs(rfc3548.isb32(bad_s), False)
            self.assertIs(rfc3548.isb32(bad_b), False)
            for i in range(size):
                bad_s = make_string(i, size, 'A', '™')
                bad_b = bad_s.encode('utf-8')
                self.assertEqual(len(bad_s), size)
                self.assertEqual(len(bad_b), size + 2)
                self.assertIs(rfc3548.isb32(bad_s), False)
                self.assertIs(rfc3548.isb32(bad_b), False)
            for i in range(size - 2):
                bad_s = make_string(i, size - 2, 'A', '™')
                bad_b = bad_s.encode('utf-8')
                self.assertEqual(len(bad_s), size - 2)
                self.assertEqual(len(bad_b), size)
                self.assertIs(rfc3548.isb32(bad_s), False)
                self.assertIs(rfc3548.isb32(bad_b), False)

    def test_random_id(self):
        with self.assertRaises(TypeError) as cm:
            rfc3548.random_id(15.0)
        self.assertEqual(
            str(cm.exception),
            'integer argument expected, got float'
        )
        with self.assertRaises(TypeError) as cm:
            rfc3548.random_id('15')
        self.assertEqual(
            str(cm.exception),
            "'str' object cannot be interpreted as an integer"
        )
        with self.assertRaises(TypeError) as cm:
            rfc3548.random_id([])
        self.assertEqual(
            str(cm.exception),
            "numbytes must be an int; got <class 'list'>"
        )

        with self.assertRaises(ValueError) as cm:
            rfc3548.random_id(4)
        self.assertEqual(
            str(cm.exception),
            'numbytes is 4, need 5 <= numbytes <= 60'
        )
        with self.assertRaises(ValueError) as cm:
            rfc3548.random_id(29)
        self.assertEqual(
            str(cm.exception),
            'numbytes is 29, need numbytes % 5 == 0'
        )

        _id = rfc3548.random_id()
        self.assertIsInstance(_id, str)
        self.assertEqual(len(_id), 24)
        data = rfc3548.b32dec(_id)
        self.assertIsInstance(data, bytes)
        self.assertEqual(len(data), 15)
        self.assertEqual(rfc3548.b32enc(data), _id)

        _id = rfc3548.random_id(15)
        self.assertIsInstance(_id, str)
        self.assertEqual(len(_id), 24)
        data = rfc3548.b32dec(_id)
        self.assertIsInstance(data, bytes)
        self.assertEqual(len(data), 15)
        self.assertEqual(rfc3548.b32enc(data), _id)

        _id = rfc3548.random_id(numbytes=15)
        self.assertIsInstance(_id, str)
        self.assertEqual(len(_id), 24)
        data = rfc3548.b32dec(_id)
        self.assertIsInstance(data, bytes)
        self.assertEqual(len(data), 15)
        self.assertEqual(rfc3548.b32enc(data), _id)

        for size in BIN_SIZES:
            _id = rfc3548.random_id(size)
            self.assertIsInstance(_id, str)
            self.assertEqual(len(_id), size * 8 // 5)
            data = rfc3548.b32dec(_id)
            self.assertIsInstance(data, bytes)
            self.assertEqual(len(data), size)
            self.assertEqual(rfc3548.b32enc(data), _id)

        # Sanity check on their randomness:
        count = 5000
        accum = set(rfc3548.random_id() for i in range(count))
        self.assertEqual(len(accum), count)

