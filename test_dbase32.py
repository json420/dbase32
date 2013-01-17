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

assert hasattr(dbase32, 'db32enc')
assert hasattr(dbase32, 'db32dec')


random = SystemRandom()
possible = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
assert ''.join(sorted(set(possible))) == possible


# B32: RFC-3548 Base32: binary sort order will not match encoded, oh noes!
# [removes 0, 1, 8, 9]
B32_START = 50
B32_END = 90
B32_FORWARD = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
B32_REVERSE = (
     26,  # 50 '2' [ 0]
     27,  # 51 '3' [ 1]
     28,  # 52 '4' [ 2]
     29,  # 53 '5' [ 3]
     30,  # 54 '6' [ 4]
     31,  # 55 '7' [ 5]
    255,  # 56 '8' [ 6]
    255,  # 57 '9' [ 7]
    255,  # 58 ':' [ 8]
    255,  # 59 ';' [ 9]
    255,  # 60 '<' [10]
    255,  # 61 '=' [11]
    255,  # 62 '>' [12]
    255,  # 63 '?' [13]
    255,  # 64 '@' [14]
      0,  # 65 'A' [15]
      1,  # 66 'B' [16]
      2,  # 67 'C' [17]
      3,  # 68 'D' [18]
      4,  # 69 'E' [19]
      5,  # 70 'F' [20]
      6,  # 71 'G' [21]
      7,  # 72 'H' [22]
      8,  # 73 'I' [23]
      9,  # 74 'J' [24]
     10,  # 75 'K' [25]
     11,  # 76 'L' [26]
     12,  # 77 'M' [27]
     13,  # 78 'N' [28]
     14,  # 79 'O' [29]
     15,  # 80 'P' [30]
     16,  # 81 'Q' [31]
     17,  # 82 'R' [32]
     18,  # 83 'S' [33]
     19,  # 84 'T' [34]
     20,  # 85 'U' [35]
     21,  # 86 'V' [36]
     22,  # 87 'W' [37]
     23,  # 88 'X' [38]
     24,  # 89 'Y' [39]
     25,  # 90 'Z' [40]
)


def b32enc_p(data):
    return dbase32.encode_x(data, B32_FORWARD)


def b32dec_p(text):
    return dbase32.decode_x(text, B32_REVERSE, B32_START, B32_END)


class TestConstants(TestCase):
    def test_max(self):
        self.assertEqual(dbase32.MAX_BIN_LEN % 5, 0)
        self.assertEqual(dbase32.MAX_TXT_LEN % 8, 0)
        self.assertEqual(dbase32.MAX_BIN_LEN, dbase32.MAX_TXT_LEN * 5 // 8)

    def test_start_end(self):
        self.assertEqual(dbase32.DB32_START, ord(dbase32.DB32_FORWARD[0]))
        self.assertEqual(dbase32.DB32_START, ord(min(dbase32.DB32_FORWARD)))
        self.assertEqual(dbase32.DB32_END, ord(dbase32.DB32_FORWARD[-1]))
        self.assertEqual(dbase32.DB32_END, ord(max(dbase32.DB32_FORWARD)))
        stop = dbase32.DB32_END + 1
        self.assertEqual(
            stop - dbase32.DB32_START,
            len(dbase32.DB32_REVERSE)
        )

    def test_forward(self):
        self.assertEqual(''.join(sorted(set(possible))), possible)
        self.assertEqual(len(possible), 36)
        self.assertEqual(
            ''.join(sorted(set(dbase32.DB32_FORWARD))),
            dbase32.DB32_FORWARD
        )
        self.assertEqual(
            set(dbase32.DB32_FORWARD),
            set(possible) - set('012Z')
        )
        self.assertEqual(len(dbase32.DB32_FORWARD), 32)

    def test_reverse(self):
        self.assertEqual(dbase32.DB32_REVERSE[0], 0)
        self.assertEqual(dbase32.DB32_REVERSE[-1], 31)
        offset = ord(dbase32.DB32_FORWARD[0])
        yes = 0
        no = 0
        for (i, value) in enumerate(dbase32.DB32_REVERSE):
            char = chr(i + offset)
            if char in dbase32.DB32_FORWARD:
                self.assertEqual(value, yes)
                yes += 1
            else:
                self.assertEqual(value, 255)
                no += 1
        self.assertEqual(yes, 32)
        self.assertEqual(len(dbase32.DB32_REVERSE) - no, 32)
        self.assertEqual(len(dbase32.DB32_REVERSE), 39)


class TestFunctions(TestCase):
    def test_encode_x(self):
        """
        Test encode_x() with the standard RFC-3548 base32 tables.

        See b32enc_p() defined above.
        """
        # A few static value sanity checks:
        self.assertEqual(b32enc_p(b'\x00\x00\x00\x00\x00'), 'AAAAAAAA')
        self.assertEqual(b32enc_p(b'\xff\xff\xff\xff\xff'), '77777777')
        self.assertEqual(b32enc_p(b'\x00' * 60), 'A' * 96)
        self.assertEqual(b32enc_p(b'\xff' * 60), '7' * 96)

        # Compare against base64.b32encode() from stdlib:
        for size in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]:
            for i in range(100):
                data = os.urandom(size)
                self.assertEqual(
                    b32enc_p(data),
                    b32encode(data).decode('utf-8')
                )

    def test_decode_x(self):
        """
        Test decode_x() with the standard RFC-3548 base32 tables.

        See b32dec_p() defined above.
        """
        # A few static value sanity checks:
        self.assertEqual(b32dec_p('AAAAAAAA'), b'\x00\x00\x00\x00\x00')
        self.assertEqual(b32dec_p('77777777'), b'\xff\xff\xff\xff\xff')
        self.assertEqual(b32dec_p('A' * 96), b'\x00' * 60)
        self.assertEqual(b32dec_p('7' * 96), b'\xff' * 60)

        # Compare against base64.b32decode() from stdlib:
        for size in [8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96]:
            for i in range(100):
                text = ''.join(random.choice(B32_FORWARD) for n in range(size))
                assert len(text) == size
                self.assertEqual(
                    b32dec_p(text),
                    b32decode(text.encode('utf-8'))
                )

    def check_db32enc_common(self, db32enc):
        """
        Encoder tests both the Python and the C implementations must pass.
        """ 
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

    def test_dbenc32_p(self):
        """
        Test the pure-Python implementation of db32enc().
        """
        self.check_db32enc_common(dbase32.db32enc_p)

    def test_db32enc_c(self):
        """
        Test the C implementation of db32enc().
        """
        if not hasattr(dbase32, 'db32enc_c'):
            self.skipTest('cannot import `_dbase32` C extension')

        self.check_db32enc_common(dbase32.db32enc_c)

        # Compare against the Python version db32enc_p
        for size in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]:
            for i in range(1000):
                data = os.urandom(size)
                self.assertEqual(
                    dbase32.db32enc_c(data),
                    dbase32.db32enc_p(data)
                )

    def check_db32dec_common(self, db32dec):
        """
        Decoder tests both the Python and the C implementations must pass.
        """    
        # Test when len(text) is too small:
        with self.assertRaises(ValueError) as cm:
            db32dec('')
        self.assertEqual(
            str(cm.exception),
            'len(text) is 0, need 8 <= len(text) <= 96'
        )
        with self.assertRaises(ValueError) as cm:
            db32dec('-seven-')
        self.assertEqual(
            str(cm.exception),
            'len(text) is 7, need 8 <= len(text) <= 96'
        )

        # Test when len(text) is too big:
        with self.assertRaises(ValueError) as cm:
            db32dec('A' * 97)
        self.assertEqual(
            str(cm.exception),
            'len(text) is 97, need 8 <= len(text) <= 96'
        )

        # Test when len(text) % 8 != 0:
        with self.assertRaises(ValueError) as cm:
            db32dec('A' * 65)
        self.assertEqual(
            str(cm.exception),
            'len(text) is 65, need len(text) % 8 == 0'
        )

        # Test with invalid base32 characters:
        with self.assertRaises(ValueError) as cm:
            db32dec('CDEFCDE2')
        self.assertEqual(str(cm.exception), "invalid base32 letter: 2")
        with self.assertRaises(ValueError) as cm:
            db32dec('CDEFCDE=')
        self.assertEqual(str(cm.exception), "invalid base32 letter: =")
        with self.assertRaises(ValueError) as cm:
            db32dec('CDEFCDEZ')
        self.assertEqual(str(cm.exception), "invalid base32 letter: Z")

        # Test a few handy static values:
        self.assertEqual(db32dec('33333333'), b'\x00\x00\x00\x00\x00')
        self.assertEqual(db32dec('YYYYYYYY'), b'\xff\xff\xff\xff\xff')
        self.assertEqual(db32dec('3' * 96), b'\x00' * 60)
        self.assertEqual(db32dec('Y' * 96), b'\xff' * 60)

    def test_db32dec_p(self):
        """
        Test the pure-Python implementation of db32enc().
        """
        self.check_db32dec_common(dbase32.db32dec_p)

    def test_db32dec_c(self):
        """
        Test the C implementation of db32enc().
        """
        if not hasattr(dbase32, 'db32dec_c'):
            self.skipTest('cannot import `_dbase32` C extension')

        self.check_db32dec_common(dbase32.db32dec_c)

        # Compare against the dbase32.db32dec_p pure-Python version:
        for size in [8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96]:
            for i in range(100):
                text = ''.join(
                    random.choice(dbase32.DB32_FORWARD)
                    for n in range(size)
                )
                assert len(text) == size
                self.assertEqual(
                    dbase32.db32dec_c(text),
                    dbase32.db32dec_p(text)
                )

