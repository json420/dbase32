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
Unit tests for `dbase32` module.
"""

from unittest import TestCase
import os
from base64 import b32encode, b32decode
from random import SystemRandom

import dbase32


random = SystemRandom()
possible = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
assert ''.join(sorted(set(possible))) == possible


# Standard RFC-3548 base32 alphabet
base32_forward = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'

base32_reverse = (
     26,  # 50 '2'
     27,  # 51 '3'
     28,  # 52 '4'
     29,  # 53 '5'
     30,  # 54 '6'
     31,  # 55 '7'
    255,  # 56 '8'
    255,  # 57 '9'
    255,  # 58 ':'
    255,  # 59 ';'
    255,  # 60 '<'
    255,  # 61 '='
    255,  # 62 '>'
    255,  # 63 '?'
    255,  # 64 '@'
      0,  # 65 'A'
      1,  # 66 'B'
      2,  # 67 'C'
      3,  # 68 'D'
      4,  # 69 'E'
      5,  # 70 'F'
      6,  # 71 'G'
      7,  # 72 'H'
      8,  # 73 'I'
      9,  # 74 'J'
     10 ,  # 75 'K'
     11,  # 76 'L'
     12,  # 77 'M'
     13,  # 78 'N'
     14,  # 79 'O'
     15,  # 80 'P'
     16,  # 81 'Q'
     17,  # 82 'R'
     18,  # 83 'S'
     19,  # 84 'T'
     20,  # 85 'U'
     21,  # 86 'V'
     22,  # 87 'W'
     23,  # 88 'X'
     24,  # 89 'Y'
     25,  # 90 'Z'
)


class TestConstants(TestCase):
    def test_forward(self):
        self.assertEqual(''.join(sorted(set(possible))), possible)
        self.assertEqual(len(possible), 36)
        self.assertEqual(
            ''.join(sorted(set(dbase32.forward))),
            dbase32.forward
        )
        self.assertEqual(
            set(dbase32.forward),
            set(possible) - set('01IO')
        )
        self.assertEqual(len(dbase32.forward), 32)

    def test_reverse(self):
        self.assertEqual(dbase32.reverse[0], 0)
        self.assertEqual(dbase32.reverse[-1], 31)
        offset = ord(dbase32.forward[0])
        yes = 0
        no = 0
        for (i, value) in enumerate(dbase32.reverse):
            char = chr(i + offset)
            if char in dbase32.forward:
                self.assertEqual(value, yes)
                yes += 1
            else:
                self.assertEqual(value, 255)
                no += 1
        self.assertEqual(yes, 32)
        self.assertEqual(len(dbase32.reverse) - no, 32)
        self.assertEqual(len(dbase32.reverse), 41)

    def test_start_stop(self):
        self.assertEqual(dbase32.start, ord(dbase32.forward[0]))
        self.assertEqual(dbase32.stop, ord(dbase32.forward[-1]) + 1)
        self.assertEqual(dbase32.stop - dbase32.start, len(dbase32.reverse))


class TestFunctions(TestCase):
    def test_enc(self):
        # Test when len(data) is too small:
        with self.assertRaises(ValueError) as cm:
            dbase32.enc(b'')
        self.assertEqual(str(cm.exception), 'need 5 <= len(data) <= 60')
        with self.assertRaises(ValueError) as cm:
            dbase32.enc(b'four')
        self.assertEqual(str(cm.exception), 'need 5 <= len(data) <= 60')

        # Test when len(data) is too big:
        with self.assertRaises(ValueError) as cm:
            dbase32.enc(b'B' * 61)
        self.assertEqual(str(cm.exception), 'need 5 <= len(data) <= 60')

        # Test when len(data) % 5 != 0:
        with self.assertRaises(ValueError) as cm:
            dbase32.enc(b'B' * 41)
        self.assertEqual(str(cm.exception), 'len(data) % 5 != 0')

        # Test a few handy static values:
        self.assertEqual(dbase32.enc(b'\x00\x00\x00\x00\x00'), '22222222')
        self.assertEqual(dbase32.enc(b'\xff\xff\xff\xff\xff'), 'ZZZZZZZZ')
        self.assertEqual(dbase32.enc(b'\x00' * 60), '2' * 96)
        self.assertEqual(dbase32.enc(b'\xff' * 60), 'Z' * 96)

        # Same, but this time using the standard base32 alphabet:
        self.assertEqual(
            dbase32.enc(b'\x00\x00\x00\x00\x00', base32_forward),
            'AAAAAAAA'
        )
        self.assertEqual(
            dbase32.enc(b'\xff\xff\xff\xff\xff', base32_forward),
            '77777777'
        )
        self.assertEqual(
            dbase32.enc(b'\x00' * 60, base32_forward),
            'A' * 96
        )
        self.assertEqual(
            dbase32.enc(b'\xff' * 60, base32_forward),
            '7' * 96
        )

        # Compare against base64.b32encode() from stdlib:
        for size in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]:
            for i in range(100):
                data = os.urandom(size)
                self.assertEqual(
                    dbase32.enc(data, base32_forward),
                    b32encode(data).decode('utf-8')
                )

    def test_dec(self):
        # Test when len(text) is too small:
        with self.assertRaises(ValueError) as cm:
            dbase32.dec('')
        self.assertEqual(str(cm.exception), 'need 8 <= len(text) <= 96')
        with self.assertRaises(ValueError) as cm:
            dbase32.dec('-seven-')
        self.assertEqual(str(cm.exception), 'need 8 <= len(text) <= 96')

        # Test when len(text) is too big:
        with self.assertRaises(ValueError) as cm:
            dbase32.dec('A' * 97)
        self.assertEqual(str(cm.exception), 'need 8 <= len(text) <= 96')

        # Test when len(text) % 8 != 0:
        with self.assertRaises(ValueError) as cm:
            dbase32.dec('A' * 65)
        self.assertEqual(str(cm.exception), 'len(text) % 8 != 0')

        # Test a few handy static values:
        self.assertEqual(dbase32.dec('22222222'), b'\x00\x00\x00\x00\x00')
        self.assertEqual(dbase32.dec('ZZZZZZZZ'), b'\xff\xff\xff\xff\xff')
        self.assertEqual(dbase32.dec('2' * 96), b'\x00' * 60)
        self.assertEqual(dbase32.dec('Z' * 96), b'\xff' * 60)

        # Same, but this time using the standard base32 alphabet:
        self.assertEqual(
            dbase32.dec('AAAAAAAA', base32_reverse),
            b'\x00\x00\x00\x00\x00'
        )
        self.assertEqual(
            dbase32.dec('77777777', base32_reverse),
            b'\xff\xff\xff\xff\xff'
        )
        self.assertEqual(
            dbase32.dec('A' * 96, base32_reverse),
            b'\x00' * 60
        )
        self.assertEqual(
            dbase32.dec('7' * 96, base32_reverse),
            b'\xff' * 60
        )

        # Compare against base64.b32decode() from stdlib:
        for size in [8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96]:
            for i in range(100):
                text = ''.join(random.choice(base32_forward) for n in range(size))
                assert len(text) == size
                self.assertEqual(
                    dbase32.dec(text, base32_reverse),
                    b32decode(text.encode('utf-8'))
                )

