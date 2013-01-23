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
        self.assertIsInstance(dbase32.DB32_REVERSE, tuple)
        self.assertEqual(len(dbase32.DB32_REVERSE), 256)


class TestFunctions(TestCase):
    def test_b32enc(self):
        """
        Test encode_x() with the standard RFC-3548 base32 tables.
        """
        # A few static value sanity checks:
        self.assertEqual(dbase32.b32enc(b'\x00\x00\x00\x00\x00'), 'AAAAAAAA')
        self.assertEqual(dbase32.b32enc(b'\xff\xff\xff\xff\xff'), '77777777')
        self.assertEqual(dbase32.b32enc(b'\x00' * 60), 'A' * 96)
        self.assertEqual(dbase32.b32enc(b'\xff' * 60), '7' * 96)

        # Compare against base64.b32encode() from stdlib:
        for size in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]:
            for i in range(100):
                data = os.urandom(size)
                self.assertEqual(
                    dbase32.b32enc(data),
                    b32encode(data).decode('utf-8')
                )

    def test_b32dec(self):
        """
        Test decode_x() with the standard RFC-3548 base32 tables.
        """
        # A few static value sanity checks:
        self.assertEqual(dbase32.b32dec('AAAAAAAA'), b'\x00\x00\x00\x00\x00')
        self.assertEqual(dbase32.b32dec('77777777'), b'\xff\xff\xff\xff\xff')
        self.assertEqual(dbase32.b32dec('A' * 96), b'\x00' * 60)
        self.assertEqual(dbase32.b32dec('7' * 96), b'\xff' * 60)

        # Compare against base64.b32decode() from stdlib:
        for size in [8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96]:
            for i in range(100):
                text = ''.join(
                    random.choice(dbase32.B32_FORWARD) for n in range(size)
                )
                assert len(text) == size
                self.assertEqual(
                    dbase32.b32dec(text),
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

    def test_roundtrip_c(self):
        """
        Test encode/decode round-trip with C implementation.
        """
        if not hasattr(dbase32, 'db32enc_c'):
            self.skipTest('cannot import `_dbase32` C extension')

        # The C implementation is wicked fast, so let's test a *lot* of values:
        for size in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]:
            for i in range(10000):
                data = os.urandom(size)
                self.assertEqual(
                    dbase32.db32dec_c(dbase32.db32enc_c(data)),
                    data
                )

