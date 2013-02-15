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
from random import SystemRandom
import base64
from collections import Counter, namedtuple

import dbase32
from dbase32 import fallback, misc

# True if the C extension is available
try:
    import _dbase32
    C_EXT_AVAIL = True
except ImportError:
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
    def test_db32alphabet(self):
        self.assertIsInstance(dbase32.DB32ALPHABET, str)
        self.assertEqual(dbase32.DB32ALPHABET, fallback.DB32_FORWARD)

    def test_max(self):
        self.assertIsInstance(dbase32.MAX_BIN_LEN, int)
        self.assertEqual(dbase32.MAX_BIN_LEN, fallback.MAX_BIN_LEN)
        self.assertIsInstance(dbase32.MAX_TXT_LEN, int)
        self.assertEqual(dbase32.MAX_TXT_LEN, fallback.MAX_TXT_LEN)

    def test_random(self):
        self.assertIsInstance(dbase32.RANDOM_BITS, int)
        self.assertEqual(dbase32.RANDOM_BITS % 40, 0)

        self.assertIsInstance(dbase32.RANDOM_BYTES, int)
        self.assertEqual(dbase32.RANDOM_BYTES, dbase32.RANDOM_BITS // 8)
        self.assertEqual(dbase32.RANDOM_BYTES % 5, 0)

        self.assertIsInstance(dbase32.RANDOM_B32LEN, int)
        self.assertEqual(dbase32.RANDOM_B32LEN, dbase32.RANDOM_BITS // 5)
        self.assertEqual(dbase32.RANDOM_B32LEN % 8, 0)

    def test_db32enc_alias(self):
        if C_EXT_AVAIL:
            self.assertIs(dbase32.db32enc, _dbase32.db32enc)
            self.assertIsNot(dbase32.db32enc, fallback.db32enc)
        else:
            self.assertIs(dbase32.db32enc, fallback.db32enc)

    def test_db32dec_alias(self):
        if C_EXT_AVAIL:
            self.assertIs(dbase32.db32dec, _dbase32.db32dec)
            self.assertIsNot(dbase32.db32dec, fallback.db32dec)
        else:
            self.assertIs(dbase32.db32dec, fallback.db32dec)

    def test_isdb32_alias(self):
        if C_EXT_AVAIL:
            self.assertIs(dbase32.isdb32, _dbase32.isdb32)
            self.assertIsNot(dbase32.isdb32, fallback.isdb32)
        else:
            self.assertIs(dbase32.isdb32, fallback.isdb32)

    def test_check_db32_alias(self):
        if C_EXT_AVAIL:
            self.assertIs(dbase32.check_db32, _dbase32.check_db32)
            self.assertIsNot(dbase32.check_db32, fallback.check_db32)
        else:
            self.assertIs(dbase32.check_db32, fallback.check_db32)

    def test_random_id_alias(self):
        if C_EXT_AVAIL:
            self.assertIs(dbase32.random_id, _dbase32.random_id)
            self.assertIsNot(dbase32.random_id, fallback.random_id)
        else:
            self.assertIs(dbase32.random_id, fallback.random_id)


class TestFunctions(TestCase):
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

    def check_db32enc(self, db32enc):
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

        # Test with wrong type:
        good = b'Bytes'
        self.assertEqual(db32enc(good), 'BCVQBSEM')
        bad = good.decode('utf-8')
        with self.assertRaises(TypeError) as cm:
            db32enc(bad)
        self.assertEqual(
            str(cm.exception),
            "'str' does not support the buffer interface"
        )

    def test_db32enc_p(self):
        """
        Test the pure-Python implementation of db32enc().
        """
        self.check_db32enc(fallback.db32enc)

    def test_db32enc_c(self):
        """
        Test the C implementation of db32enc().
        """
        self.skip_if_no_c_ext()
        self.check_db32enc(_dbase32.db32enc)

        # Compare against the Python version of db32enc
        for size in BIN_SIZES:
            for i in range(1000):
                data = os.urandom(size)
                self.assertEqual(
                    _dbase32.db32enc(data),
                    fallback.db32enc(data)
                )

    def check_db32dec(self, db32dec):
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
        self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: 2')
        with self.assertRaises(ValueError) as cm:
            db32dec('CDEFCDE=')
        self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: =')
        with self.assertRaises(ValueError) as cm:
            db32dec('CDEFCDEZ')
        self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: Z')

        # Test that it stops at the first invalid letter:
        with self.assertRaises(ValueError) as cm:
            db32dec('2ZZZZZZZ')
        self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: 2')
        with self.assertRaises(ValueError) as cm:
            db32dec('AAAAAA=Z')
        self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: =')
        with self.assertRaises(ValueError) as cm:
            db32dec('CDEZ=2=2')
        self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: Z')

        # Test a few handy static values:
        self.assertEqual(db32dec('33333333'), b'\x00\x00\x00\x00\x00')
        self.assertEqual(db32dec('YYYYYYYY'), b'\xff\xff\xff\xff\xff')
        self.assertEqual(db32dec('3' * 96), b'\x00' * 60)
        self.assertEqual(db32dec('Y' * 96), b'\xff' * 60)

        # Test invalid letter at each possible position in the string
        for size in TXT_SIZES:
            for i in range(size):
                # Test when there is a single invalid letter:
                txt = make_string(i, size, 'A', '/')
                with self.assertRaises(ValueError) as cm:
                    db32dec(txt)
                self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: /')
                txt = make_string(i, size, 'A', '.')
                with self.assertRaises(ValueError) as cm:
                    db32dec(txt)
                self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: .')

                # Test that it stops at the *first* invalid letter:
                txt = make_string(i, size, 'A', '/', '.')
                with self.assertRaises(ValueError) as cm:
                    db32dec(txt)
                self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: /')
                txt = make_string(i, size, 'A', '.', '/')
                with self.assertRaises(ValueError) as cm:
                    db32dec(txt)
                self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: .')

        # Test a slew of no-no letters:
        for L in BAD_LETTERS:
            txt = ('A' * 7) + L
            with self.assertRaises(ValueError) as cm:
                db32dec(txt)
            self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: ' + L)

        # Test with wrong type:
        good = '3' * 8
        self.assertEqual(db32dec(good), b'\x00\x00\x00\x00\x00')
        bad = good.encode('utf-8')
        with self.assertRaises(TypeError) as cm:
            db32dec(bad)
        self.assertEqual(str(cm.exception), 'must be str, not bytes')

    def test_db32dec_p(self):
        """
        Test the pure-Python implementation of db32enc().
        """
        self.check_db32dec(fallback.db32dec)

    def test_db32dec_c(self):
        """
        Test the C implementation of db32enc().
        """
        self.skip_if_no_c_ext()
        self.check_db32dec(_dbase32.db32dec)

        # Compare against the fallback.db32dec Python version:
        for size in TXT_SIZES:
            for i in range(100):
                text = ''.join(
                    random.choice(fallback.DB32_FORWARD)
                    for n in range(size)
                )
                assert len(text) == size
                self.assertEqual(
                    _dbase32.db32dec(text),
                    fallback.db32dec(text)
                )

    def test_sort_p(self):
        """
        Confirm assumptions about RFC-3548 sort-order, test D-Base32 sort-order.
        """
        ids = [os.urandom(30) for i in range(1000)]
        ids.extend(os.urandom(15) for i in range(1500))

        orig = tuple(
            Tup(
                data,
                base64.b32encode(data).decode('utf-8'),
                fallback.db32enc(data)
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
            self.assertEqual(t.db32, fallback.db32enc(t.data))

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
        Test binary vs D-Base32 sort order, with a *lot* of values.
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

    def test_roundtrip_p(self):
        """
        Test encode/decode round-trip with Python implementation.
        """
        for size in BIN_SIZES:
            for i in range(1000):
                data = os.urandom(size)
                self.assertEqual(
                    fallback.db32dec(fallback.db32enc(data)),
                    data
                )

    def test_roundtrip_c(self):
        """
        Test encode/decode round-trip with C implementation.
        """
        self.skip_if_no_c_ext()

        # The C implementation is wicked fast, so let's test a *lot* of values:
        for size in BIN_SIZES:
            for i in range(50 * 1000):
                data = os.urandom(size)
                self.assertEqual(
                    _dbase32.db32dec(_dbase32.db32enc(data)),
                    data
                )

    def check_isdb32(self, isdb32):
        for size in TXT_SIZES:
            self.assertIs(isdb32('A' * (size - 1)), False)
            self.assertIs(isdb32('A' * (size + 1)), False)
            self.assertIs(isdb32('A' * size), True)
            good = ''.join(
                random.choice(fallback.DB32_FORWARD)
                for n in range(size)
            )
            self.assertIs(isdb32(good), True)
            for L in BAD_LETTERS:
                bad = good[:-1] + L
                self.assertEqual(len(bad), size)
                self.assertIs(isdb32(bad), False)
            for i in range(size):
                bad = make_string(i, size, 'A', '/')
                self.assertEqual(len(bad), size)
                self.assertIs(isdb32(bad), False)
                g = make_string(i, size, 'A', 'B')
                self.assertIs(isdb32(g), True)
            for i in range(size):
                for L in BAD_LETTERS:
                    bad = make_string(i, size, 'A', L)
                    self.assertEqual(len(bad), size)
                    self.assertIs(isdb32(bad), False)

        # Test with wrong type:
        good = '3' * 8
        self.assertIs(isdb32(good), True)
        bad = good.encode('utf-8')
        with self.assertRaises(TypeError) as cm:
            isdb32(bad)
        self.assertEqual(str(cm.exception), 'must be str, not bytes')

    def test_isdb32_p(self):
        self.check_isdb32(fallback.isdb32)

    def test_isdb32_c(self):
        self.skip_if_no_c_ext()
        self.check_isdb32(_dbase32.isdb32)

    def check_check_db32(self, check_db32):
        """
        Tests both Python and C versions of `check_db32()` must pass.
        """
        # Test with wrong type:
        good = '3' * 8
        self.assertIsNone(check_db32(good))
        bad = good.encode('utf-8')
        with self.assertRaises(TypeError) as cm:
            check_db32(bad)
        self.assertEqual(str(cm.exception), 'must be str, not bytes')
  
        # Test when len(text) is too small:
        with self.assertRaises(ValueError) as cm:
            check_db32('')
        self.assertEqual(
            str(cm.exception),
            'len(text) is 0, need 8 <= len(text) <= 96'
        )
        with self.assertRaises(ValueError) as cm:
            check_db32('-seven-')
        self.assertEqual(
            str(cm.exception),
            'len(text) is 7, need 8 <= len(text) <= 96'
        )

        # Test when len(text) is too big:
        with self.assertRaises(ValueError) as cm:
            check_db32('A' * 97)
        self.assertEqual(
            str(cm.exception),
            'len(text) is 97, need 8 <= len(text) <= 96'
        )

        # Test when len(text) % 8 != 0:
        with self.assertRaises(ValueError) as cm:
            check_db32('A' * 65)
        self.assertEqual(
            str(cm.exception),
            'len(text) is 65, need len(text) % 8 == 0'
        )

        # Test with invalid base32 characters:
        with self.assertRaises(ValueError) as cm:
            check_db32('CDEFCDE2')
        self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: 2')
        with self.assertRaises(ValueError) as cm:
            check_db32('CDEFCDE=')
        self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: =')
        with self.assertRaises(ValueError) as cm:
            check_db32('CDEFCDEZ')
        self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: Z')

        # Test that it stops at the first invalid letter:
        with self.assertRaises(ValueError) as cm:
            check_db32('2ZZZZZZZ')
        self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: 2')
        with self.assertRaises(ValueError) as cm:
            check_db32('AAAAAA=Z')
        self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: =')
        with self.assertRaises(ValueError) as cm:
            check_db32('CDEZ=2=2')
        self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: Z')

        # Test a few handy static values:
        self.assertIsNone(check_db32('33333333'))
        self.assertIsNone(check_db32('YYYYYYYY'))
        self.assertIsNone(check_db32('3' * 96))
        self.assertIsNone(check_db32('Y' * 96))

        # Test invalid letter at each possible position in the string
        for size in TXT_SIZES:
            for i in range(size):
                # Test when there is a single invalid letter:
                txt = make_string(i, size, 'A', '/')
                with self.assertRaises(ValueError) as cm:
                    check_db32(txt)
                self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: /')
                txt = make_string(i, size, 'A', '.')
                with self.assertRaises(ValueError) as cm:
                    check_db32(txt)
                self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: .')

                # Test that it stops at the *first* invalid letter:
                txt = make_string(i, size, 'A', '/', '.')
                with self.assertRaises(ValueError) as cm:
                    check_db32(txt)
                self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: /')
                txt = make_string(i, size, 'A', '.', '/')
                with self.assertRaises(ValueError) as cm:
                    check_db32(txt)
                self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: .')

        # Test a slew of no-no letters:
        for L in BAD_LETTERS:
            txt = ('A' * 7) + L
            with self.assertRaises(ValueError) as cm:
                check_db32(txt)
            self.assertEqual(str(cm.exception), 'invalid D-Base32 letter: ' + L)

    def test_check_db32_p(self):
        self.check_check_db32(fallback.check_db32)

    def test_check_db32_c(self):
        self.skip_if_no_c_ext()
        self.check_check_db32(_dbase32.check_db32)

    def check_random_id(self, random_id):
        with self.assertRaises(TypeError) as cm:        
            random_id(15.0)
        self.assertEqual(
            str(cm.exception),
            'integer argument expected, got float'
        )

        with self.assertRaises(ValueError) as cm:
            random_id(4)
        self.assertEqual(
            str(cm.exception),
            'size is 4, need 5 <= size <= 60'
        )
        with self.assertRaises(ValueError) as cm:
            random_id(29)
        self.assertEqual(
            str(cm.exception),
            'size is 29, need size % 5 == 0'
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

        _id = random_id(size=dbase32.RANDOM_BYTES)
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
        count = 5000
        accum = set(random_id(15) for i in range(count))
        self.assertEqual(len(accum), count)

    def test_random_id_p(self):
        self.check_random_id(fallback.random_id)

    def test_random_id_c(self):
        self.skip_if_no_c_ext()
        self.check_random_id(_dbase32.random_id)
