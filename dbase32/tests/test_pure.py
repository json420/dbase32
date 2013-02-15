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
Unit tests for `dbase32.pure` module.
"""

from unittest import TestCase
import os
import base64
from collections import Counter, namedtuple

from dbase32 import misc
from dbase32 import pure

possible = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
assert ''.join(sorted(set(possible))) == possible
assert len(possible) == 36


class TestConstants(TestCase):
    def test_max(self):
        self.assertIsInstance(pure.MAX_BIN_LEN, int)
        self.assertIsInstance(pure.MAX_TXT_LEN, int)
        self.assertEqual(pure.MAX_BIN_LEN % 5, 0)
        self.assertEqual(pure.MAX_TXT_LEN % 8, 0)
        self.assertEqual(pure.MAX_BIN_LEN, pure.MAX_TXT_LEN * 5 // 8)

    def test_start(self):
        self.assertEqual(
            pure.DB32_START,
            ord(min(pure.DB32_FORWARD))
        )
        self.assertEqual(
            pure.DB32_START,
            ord(pure.DB32_FORWARD[0])
        )
        self.assertEqual(
            pure.DB32_START,
            misc.get_start(pure.DB32_FORWARD)
        )

    def test_end(self):
        self.assertEqual(
            pure.DB32_END,
            ord(max(pure.DB32_FORWARD))
        )
        self.assertEqual(
            pure.DB32_END,
            ord(pure.DB32_FORWARD[-1])
        )
        self.assertEqual(
            pure.DB32_END,
            misc.get_end(pure.DB32_FORWARD)
        )

    def test_forward(self):
        self.assertEqual(
            ''.join(sorted(set(pure.DB32_FORWARD))),
            pure.DB32_FORWARD
        )
        self.assertEqual(
            set(pure.DB32_FORWARD),
            set(possible) - set('012Z')
        )
        self.assertIsInstance(pure.DB32_FORWARD, str)
        self.assertEqual(len(pure.DB32_FORWARD), 32)
        self.assertEqual(pure.DB32_FORWARD, misc.gen_forward('012Z'))
        misc.check_forward(pure.DB32_FORWARD)

    def test_reverse(self):
        self.assertIsInstance(pure.DB32_REVERSE, tuple)
        self.assertEqual(len(pure.DB32_REVERSE), 256)
        self.assertEqual(min(pure.DB32_REVERSE), 0)
        self.assertEqual(max(pure.DB32_REVERSE), 255)
        self.assertEqual(
            pure.DB32_REVERSE,
            tuple(r.value for r in misc.gen_reverse(pure.DB32_FORWARD))
        )

        for (i, value) in enumerate(pure.DB32_REVERSE):
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
        self.assertEqual(set(pure.DB32_REVERSE), expected)

        counts = Counter(pure.DB32_REVERSE)
        self.assertEqual(counts[255], 256 - 32)
        for i in range(32):
            self.assertEqual(counts[i], 1)

    def test_alphabet(self):
        self.assertIsInstance(pure.DB32ALPHABET, frozenset)
        self.assertEqual(pure.DB32ALPHABET, frozenset(pure.DB32_FORWARD))
