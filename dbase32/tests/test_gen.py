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
Unit tests for `dbase32.gen` module.
"""

from unittest import TestCase

from dbase32.gen import TYPE_ERROR
from dbase32 import gen


class TestFunctions(TestCase):
    def test_possible(self):
        self.assertEqual(''.join(sorted(set(gen.POSSIBLE))), gen.POSSIBLE)
        self.assertEqual(len(gen.POSSIBLE), 36)

    def test_gen_forward(self):
        with self.assertRaises(TypeError) as cm:
            gen.gen_forward(b'0123')
        self.assertEqual(
            str(cm.exception),
            TYPE_ERROR.format('remove', str, bytes, b'0123')
        )

        with self.assertRaises(ValueError) as cm:
            gen.gen_forward('ABC')
        self.assertEqual(
            str(cm.exception),
            "len(remove) != 4: [3] 'ABC'"
        )

        with self.assertRaises(ValueError) as cm:
            gen.gen_forward('ABCDE')
        self.assertEqual(
            str(cm.exception),
            "len(remove) != 4: [5] 'ABCDE'"
        )

        with self.assertRaises(ValueError) as cm:
            gen.gen_forward('ABCA')
        self.assertEqual(
            str(cm.exception),
            "len(set(remove)) != 4: [3] 'ABCA'"
        )

        with self.assertRaises(ValueError) as cm:
            gen.gen_forward('012z')
        self.assertEqual(
            str(cm.exception),
            "remove: '012z' not a subset of '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'"
        )

        self.assertEqual(
            gen.gen_forward('4IOU'),
            '012356789ABCDEFGHJKLMNPQRSTVWXYZ'
        )
        self.assertEqual(
            gen.gen_forward('PONM'),
            '0123456789ABCDEFGHIJKLQRSTUVWXYZ'
        )
        self.assertEqual(
            gen.gen_forward('8967'),
            '012345ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        )

    def test_check_forward(self):
        bad = b'0123456789ABCDEFGHIJKLMNOPQRSTUV'
        with self.assertRaises(TypeError) as cm:
            gen.check_forward(bad)
        self.assertEqual(
            str(cm.exception),
            TYPE_ERROR.format('forward', str, bytes, bad)
        )

        bad = '3456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        with self.assertRaises(ValueError) as cm:
            gen.check_forward(bad)
        self.assertEqual(
            str(cm.exception),
            'len(forward) != 32: [33] {!r}'.format(bad)
        )

        bad = '56789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        with self.assertRaises(ValueError) as cm:
            gen.check_forward(bad)
        self.assertEqual(
            str(cm.exception),
            'len(forward) != 32: [31] {!r}'.format(bad)
        )

        bad = '45678ZABCDEFGHIJKLMNOPQRSTUVWXYZ'
        with self.assertRaises(ValueError) as cm:
            gen.check_forward(bad)
        self.assertEqual(
            str(cm.exception),
            'len(set(forward)) != 32: [31] {!r}'.format(bad)
        )

        bad = '456789abcDEFGHIJKLMNOPQRSTUVWXYZ'
        with self.assertRaises(ValueError) as cm:
            gen.check_forward(bad)
        self.assertEqual(
            str(cm.exception),
            'forward: {!r} not a subset of {!r}'.format(bad, gen.POSSIBLE)
        )

        good = '012356789ABCDEFGHJKLMNPQRSTVWXYZ'
        self.assertIs(gen.check_forward(good), good)

    def test_get_start(self):
        self.assertEqual(
            gen.get_start('3456789ABCDEFGHIJKLMNOPQRSTUVWXY'), 51
        )
        self.assertEqual(
            gen.get_start('NOPQRSTUVWXY3456789ABCDEFGHIJKLM'), 51
        )
        self.assertEqual(chr(51), '3')
        self.assertEqual(
            gen.get_start('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'), 50
        )
        self.assertEqual(
            gen.get_start('234567ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 50
        )
        self.assertEqual(chr(50), '2')

    def test_get_end(self):
        self.assertEqual(
            gen.get_end('3456789ABCDEFGHIJKLMNOPQRSTUVWXY'), 89
        )
        self.assertEqual(
            gen.get_end('NOPQRSTUVWXY3456789ABCDEFGHIJKLM'), 89
        )
        self.assertEqual(chr(89), 'Y')
        self.assertEqual(
            gen.get_end('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'), 90
        )
        self.assertEqual(
            gen.get_end('234567ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 90
        )
        self.assertEqual(chr(90), 'Z')

    def test_gen_reverse(self):
        # Dmedia-Base32:
        forward = '3456789ABCDEFGHIJKLMNOPQRSTUVWXY'
        reverse = gen.gen_reverse(forward)
        self.assertIsInstance(reverse, tuple)
        self.assertEqual(len(reverse), 256)
        for (i, r) in enumerate(reverse):
            self.assertIsInstance(r, gen.Reverse)
            self.assertEqual(r.i, i)
        count = 0
        for (i, r) in enumerate(reverse[0:51]):
            self.assertEqual(r, (i, None, 255))
            count += 1
        for (i, r) in enumerate(reverse[90:256]):
            self.assertEqual(r, (90 + i, None, 255))
            count += 1
        main = reverse[51:90]
        self.assertEqual(len(main) + count, 256)
        for r in main:
            self.assertEqual(r.key, chr(r.i))
            self.assertEqual(r.i, ord(r.key))
            if r.value != 255:
                self.assertEqual(r.value, forward.find(r.key))
        self.assertEqual(main,
            (
                (51, '3',   0),
                (52, '4',   1),
                (53, '5',   2),
                (54, '6',   3),
                (55, '7',   4),
                (56, '8',   5),
                (57, '9',   6),
                (58, ':', 255),
                (59, ';', 255),
                (60, '<', 255),
                (61, '=', 255),
                (62, '>', 255),
                (63, '?', 255),
                (64, '@', 255),
                (65, 'A',   7),
                (66, 'B',   8),
                (67, 'C',   9),
                (68, 'D',  10),
                (69, 'E',  11),
                (70, 'F',  12),
                (71, 'G',  13),
                (72, 'H',  14),
                (73, 'I',  15),
                (74, 'J',  16),
                (75, 'K',  17),
                (76, 'L',  18),
                (77, 'M',  19),
                (78, 'N',  20),
                (79, 'O',  21),
                (80, 'P',  22),
                (81, 'Q',  23),
                (82, 'R',  24),
                (83, 'S',  25),
                (84, 'T',  26),
                (85, 'U',  27),
                (86, 'V',  28),
                (87, 'W',  29),
                (88, 'X',  30),
                (89, 'Y',  31),
            )
        )

        # Standard RFC-3548 Base32:
        forward = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
        reverse = gen.gen_reverse(forward)
        self.assertIsInstance(reverse, tuple)
        self.assertEqual(len(reverse), 256)
        for (i, r) in enumerate(reverse):
            self.assertIsInstance(r, gen.Reverse)
            self.assertEqual(r.i, i)
        count = 0
        for (i, r) in enumerate(reverse[0:50]):
            self.assertEqual(r, (i, None, 255))
            count += 1
        for (i, r) in enumerate(reverse[91:256]):
            self.assertEqual(r, (91 + i, None, 255))
            count += 1
        main = reverse[50:91]
        self.assertEqual(len(main) + count, 256)
        for r in main:
            self.assertEqual(r.key, chr(r.i))
            self.assertEqual(r.i, ord(r.key))
            if r.value != 255:
                self.assertEqual(r.value, forward.find(r.key))
        self.assertEqual(main,
            (
                (50, '2',  26),
                (51, '3',  27),
                (52, '4',  28),
                (53, '5',  29),
                (54, '6',  30),
                (55, '7',  31),
                (56, '8', 255),
                (57, '9', 255),
                (58, ':', 255),
                (59, ';', 255),
                (60, '<', 255),
                (61, '=', 255),
                (62, '>', 255),
                (63, '?', 255),
                (64, '@', 255),
                (65, 'A',   0),
                (66, 'B',   1),
                (67, 'C',   2),
                (68, 'D',   3),
                (69, 'E',   4),
                (70, 'F',   5),
                (71, 'G',   6),
                (72, 'H',   7),
                (73, 'I',   8),
                (74, 'J',   9),
                (75, 'K',  10),
                (76, 'L',  11),
                (77, 'M',  12),
                (78, 'N',  13),
                (79, 'O',  14),
                (80, 'P',  15),
                (81, 'Q',  16),
                (82, 'R',  17),
                (83, 'S',  18),
                (84, 'T',  19),
                (85, 'U',  20),
                (86, 'V',  21),
                (87, 'W',  22),
                (88, 'X',  23),
                (89, 'Y',  24),
                (90, 'Z',  25),
            )
        )

    def test_rotate_left(self):
        reverse = tuple(range(256))
        self.assertEqual(gen.rotate_left(reverse, 0), reverse)

        expected = list(range(1, 256))
        expected.append(0)
        self.assertEqual(gen.rotate_left(reverse, 1), tuple(expected))

        expected = list(range(51, 256))
        expected.extend(range(51))
        self.assertEqual(gen.rotate_left(reverse, 51), tuple(expected))

    def test_count_valid(self):
        forward = gen.gen_forward(gen.REMOVE)
        reverse = gen.gen_reverse(forward)

        # Verify assupmtions about cache line distribution in non-rotated table:
        self.assertEqual(gen.count_valid(reverse), 32)
        self.assertEqual(gen.count_valid(reverse[0:64]), 7)
        self.assertEqual(gen.count_valid(reverse[64:128]), 25)
        self.assertEqual(gen.count_valid(reverse[128:192]), 0)
        self.assertEqual(gen.count_valid(reverse[192:256]), 0)

        # Test the rotated table:
        rotated = gen.rotate_left(reverse, 42)
        self.assertEqual(gen.count_valid(rotated), 32)
        self.assertEqual(gen.count_valid(rotated[0:64]), 32)
        self.assertEqual(gen.count_valid(rotated[64:128]), 0)
        self.assertEqual(gen.count_valid(rotated[128:192]), 0)
        self.assertEqual(gen.count_valid(rotated[192:256]), 0)

        # Test the rotated table re ballanced entries between 32 byte cache lines:
        self.assertEqual(gen.count_valid(rotated[0:32]), 16)
        self.assertEqual(gen.count_valid(rotated[32:64]), 16)

        # Test the count_cache_32() helper also:
        self.assertEqual(gen.count_cache_32(rotated), (16, 16))

