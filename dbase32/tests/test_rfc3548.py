# dbase32: base32-encoding with a sorted-order alphabet (for databases)
# Copyright (C) 2013 Novacut Inc
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

from dbase32 import rfc3548, gen


random = SystemRandom()


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


class TestFunctions(TestCase):
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
        for size in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]:
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
        # A few static value sanity checks:
        self.assertEqual(rfc3548.b32dec('AAAAAAAA'), b'\x00\x00\x00\x00\x00')
        self.assertEqual(rfc3548.b32dec('77777777'), b'\xff\xff\xff\xff\xff')
        self.assertEqual(rfc3548.b32dec('A' * 96), b'\x00' * 60)
        self.assertEqual(rfc3548.b32dec('7' * 96), b'\xff' * 60)

        # Compare against base64.b32decode() from stdlib:
        for size in [8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96]:
            for i in range(100):
                text = ''.join(
                    random.choice(rfc3548.B32_FORWARD) for n in range(size)
                )
                assert len(text) == size
                self.assertEqual(
                    rfc3548.b32dec(text),
                    base64.b32decode(text.encode('utf-8'))
                )

