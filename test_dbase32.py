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
from base64 import b32encode

import dbase32


possible = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
assert ''.join(sorted(set(possible))) == possible

base32_alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'


class TestConstants(TestCase):
    def test_alphabet(self):
        self.assertEqual(''.join(sorted(set(possible))), possible)
        self.assertEqual(len(possible), 36)

        self.assertEqual(
            ''.join(sorted(set(dbase32.alphabet))),
            dbase32.alphabet
        )
        self.assertEqual(
            set(dbase32.alphabet),
            set(possible) - set('01IO')
        )
        self.assertEqual(len(dbase32.alphabet), 32)

    def test_r_alphabet(self):
        self.assertEqual(dbase32.r_alphabet[0], 0)
        self.assertEqual(dbase32.r_alphabet[-1], 31)
        offset = ord(dbase32.alphabet[0])
        yes = 0
        no = 0
        for (i, value) in enumerate(dbase32.r_alphabet):
            char = chr(i + offset)
            if char in dbase32.alphabet:
                self.assertEqual(value, yes)
                yes += 1
            else:
                self.assertEqual(value, 255)
                no += 1
        self.assertEqual(yes, 32)
        self.assertEqual(len(dbase32.r_alphabet) - no, 32)
        self.assertEqual(len(dbase32.r_alphabet), 41)

    def test_start_stop(self):
        self.assertEqual(dbase32.start, ord(dbase32.alphabet[0]))
        self.assertEqual(dbase32.stop, ord(dbase32.alphabet[-1]) + 1)
        self.assertEqual(dbase32.stop - dbase32.start, len(dbase32.r_alphabet))


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
            dbase32.enc(b'\x00\x00\x00\x00\x00', base32_alphabet),
            'AAAAAAAA'
        )
        self.assertEqual(
            dbase32.enc(b'\xff\xff\xff\xff\xff', base32_alphabet),
            '77777777'
        )
        self.assertEqual(
            dbase32.enc(b'\x00' * 60, base32_alphabet),
            'A' * 96
        )
        self.assertEqual(
            dbase32.enc(b'\xff' * 60, base32_alphabet),
            '7' * 96
        )

        # Compare against base64.b32encode() from stdlib:
        for size in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]:
            for i in range(1000):
                data = os.urandom(size)
                self.assertEqual(
                    dbase32.enc(data, base32_alphabet),
                    b32encode(data).decode('utf-8')
                )

