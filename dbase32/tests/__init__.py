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

from dbase32 import misc
import dbase32


random = SystemRandom()
possible = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
assert ''.join(sorted(set(possible))) == possible
assert len(possible) == 36

TXT_SIZES = (8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96)
BAD_LETTERS = '\'"`~!#$%^&*()[]{}|+-_.,\/ 012:;<=>?@Zabcdefghijklmnopqrstuvwxyz'

# True if the C extension is avialable
C_EXT_AVAIL = hasattr(dbase32, 'db32enc_c')

# Used in test_sort_p()
Tup = namedtuple('Tup', 'data b32 db32')


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
    def test_max(self):
        self.assertIsInstance(dbase32.MAX_BIN_LEN, int)
        self.assertIsInstance(dbase32.MAX_TXT_LEN, int)
        self.assertEqual(dbase32.MAX_BIN_LEN % 5, 0)
        self.assertEqual(dbase32.MAX_TXT_LEN % 8, 0)
        self.assertEqual(dbase32.MAX_BIN_LEN, dbase32.MAX_TXT_LEN * 5 // 8)

    def test_random(self):
        self.assertIsInstance(dbase32.RANDOM_BITS, int)
        self.assertEqual(dbase32.RANDOM_BITS % 40, 0)

        self.assertIsInstance(dbase32.RANDOM_BYTES, int)
        self.assertEqual(dbase32.RANDOM_BYTES, dbase32.RANDOM_BITS // 8)
        self.assertEqual(dbase32.RANDOM_BYTES % 5, 0)

        self.assertIsInstance(dbase32.RANDOM_B32LEN, int)
        self.assertEqual(dbase32.RANDOM_B32LEN, dbase32.RANDOM_BITS // 5)
        self.assertEqual(dbase32.RANDOM_B32LEN % 8, 0)

    def test_start(self):
        self.assertEqual(
            dbase32.DB32_START,
            ord(min(dbase32.DB32_FORWARD))
        )
        self.assertEqual(
            dbase32.DB32_START,
            ord(dbase32.DB32_FORWARD[0])
        )
        self.assertEqual(
            dbase32.DB32_START,
            misc.get_start(dbase32.DB32_FORWARD)
        )

    def test_end(self):
        self.assertEqual(
            dbase32.DB32_END,
            ord(max(dbase32.DB32_FORWARD))
        )
        self.assertEqual(
            dbase32.DB32_END,
            ord(dbase32.DB32_FORWARD[-1])
        )
        self.assertEqual(
            dbase32.DB32_END,
            misc.get_end(dbase32.DB32_FORWARD)
        )

    def test_forward(self):
        self.assertEqual(
            ''.join(sorted(set(dbase32.DB32_FORWARD))),
            dbase32.DB32_FORWARD
        )
        self.assertEqual(
            set(dbase32.DB32_FORWARD),
            set(possible) - set('012Z')
        )
        self.assertIsInstance(dbase32.DB32_FORWARD, str)
        self.assertEqual(len(dbase32.DB32_FORWARD), 32)
        self.assertEqual(dbase32.DB32_FORWARD, misc.gen_forward('012Z'))

    def test_reverse(self):
        self.assertIsInstance(dbase32.DB32_REVERSE, tuple)
        self.assertEqual(len(dbase32.DB32_REVERSE), 256)
        self.assertEqual(min(dbase32.DB32_REVERSE), 0)
        self.assertEqual(max(dbase32.DB32_REVERSE), 255)
        self.assertEqual(
            dbase32.DB32_REVERSE,
            tuple(r.value for r in misc.gen_reverse(dbase32.DB32_FORWARD))
        )

        for (i, value) in enumerate(dbase32.DB32_REVERSE):
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
        self.assertEqual(set(dbase32.DB32_REVERSE), expected)

        counts = Counter(dbase32.DB32_REVERSE)
        self.assertEqual(counts[255], 256 - 32)
        for i in range(32):
            self.assertEqual(counts[i], 1)

    def test_alphabet(self):
        self.assertIsInstance(dbase32.DB32ALPHABET, frozenset)
        self.assertEqual(dbase32.DB32ALPHABET, frozenset(dbase32.DB32_FORWARD))

    def test_db32enc_alias(self):
        if C_EXT_AVAIL:
            self.assertIs(dbase32.db32enc, dbase32.db32enc_c)
            self.assertIsNot(dbase32.db32enc, dbase32.db32enc_p)
        else:
            self.assertIs(dbase32.db32enc, dbase32.db32enc_p)

    def test_db32dec_alias(self):
        if C_EXT_AVAIL:
            self.assertIs(dbase32.db32dec, dbase32.db32dec_c)
            self.assertIsNot(dbase32.db32dec, dbase32.db32dec_p)
        else:
            self.assertIs(dbase32.db32dec, dbase32.db32dec_p)

    def test_isdb32_alias(self):
        if C_EXT_AVAIL:
            self.assertIs(dbase32.isdb32, dbase32.isdb32_c)
            self.assertIsNot(dbase32.isdb32, dbase32.isdb32_p)
        else:
            self.assertIs(dbase32.isdb32, dbase32.isdb32_p)


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

    def test_db32enc_p(self):
        """
        Test the pure-Python implementation of db32enc().
        """
        self.check_db32enc_common(dbase32.db32enc_p)

    def test_db32enc_c(self):
        """
        Test the C implementation of db32enc().
        """
        self.skip_if_no_c_ext()
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

        # Test that it stops at the first invalid letter:
        with self.assertRaises(ValueError) as cm:
            db32dec('2ZZZZZZZ')
        self.assertEqual(str(cm.exception), "invalid base32 letter: 2")
        with self.assertRaises(ValueError) as cm:
            db32dec('AAAAAA=Z')
        self.assertEqual(str(cm.exception), "invalid base32 letter: =")
        with self.assertRaises(ValueError) as cm:
            db32dec('CDEZ=2=2')
        self.assertEqual(str(cm.exception), "invalid base32 letter: Z")

        # Test a few handy static values:
        self.assertEqual(db32dec('33333333'), b'\x00\x00\x00\x00\x00')
        self.assertEqual(db32dec('YYYYYYYY'), b'\xff\xff\xff\xff\xff')
        self.assertEqual(db32dec('3' * 96), b'\x00' * 60)
        self.assertEqual(db32dec('Y' * 96), b'\xff' * 60)

        # Test invalid letter at each possible position in the string
        for size in [8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96]:
            for i in range(size):
                # Test when there is a single invalid letter:
                txt = make_string(i, size, 'A', '/')
                with self.assertRaises(ValueError) as cm:
                    db32dec(txt)
                self.assertEqual(str(cm.exception), 'invalid base32 letter: /')
                txt = make_string(i, size, 'A', '.')
                with self.assertRaises(ValueError) as cm:
                    db32dec(txt)
                self.assertEqual(str(cm.exception), 'invalid base32 letter: .')

                # Test that it stops at the *first* invalid letter:
                txt = make_string(i, size, 'A', '/', '.')
                with self.assertRaises(ValueError) as cm:
                    db32dec(txt)
                self.assertEqual(str(cm.exception), 'invalid base32 letter: /')
                txt = make_string(i, size, 'A', '.', '/')
                with self.assertRaises(ValueError) as cm:
                    db32dec(txt)
                self.assertEqual(str(cm.exception), 'invalid base32 letter: .')

        # Test a slew of no-no letters:
        for L in BAD_LETTERS:
            txt = ('A' * 7) + L
            with self.assertRaises(ValueError) as cm:
                db32dec(txt)
            self.assertEqual(str(cm.exception), 'invalid base32 letter: ' + L)

    def test_db32dec_p(self):
        """
        Test the pure-Python implementation of db32enc().
        """
        self.check_db32dec_common(dbase32.db32dec_p)

    def test_db32dec_c(self):
        """
        Test the C implementation of db32enc().
        """
        self.skip_if_no_c_ext()
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
                dbase32.db32enc_p(data)
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
            self.assertEqual(t.db32, dbase32.db32enc_p(t.data))

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
            (data, dbase32.db32enc_c(data)) for data in ids
        )
        sort_by_bin = sorted(pairs, key=lambda t: t[0])
        sort_by_txt = sorted(pairs, key=lambda t: t[1])
        self.assertEqual(sort_by_bin, sort_by_txt)

    def test_roundtrip_p(self):
        """
        Test encode/decode round-trip with Python implementation.
        """
        for size in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]:
            for i in range(1000):
                data = os.urandom(size)
                self.assertEqual(
                    dbase32.db32dec_p(dbase32.db32enc_p(data)),
                    data
                )

    def test_roundtrip_c(self):
        """
        Test encode/decode round-trip with C implementation.
        """
        self.skip_if_no_c_ext()

        # The C implementation is wicked fast, so let's test a *lot* of values:
        for size in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]:
            for i in range(50 * 1000):
                data = os.urandom(size)
                self.assertEqual(
                    dbase32.db32dec_c(dbase32.db32enc_c(data)),
                    data
                )

    def check_isdb32_common(self, isdb32):
        for size in TXT_SIZES:
            self.assertIs(isdb32('A' * (size - 1)), False)
            self.assertIs(isdb32('A' * (size + 1)), False)
            self.assertIs(isdb32('A' * size), True)
            good = ''.join(
                random.choice(dbase32.DB32_FORWARD)
                for n in range(size)
            )
            self.assertIs(isdb32(good), True)
            for L in BAD_LETTERS:
                bad = good[:-1] + L
                self.assertEqual(len(bad), size)
                self.assertIs(isdb32(bad), False)

    def test_isdb32_p(self):
        self.check_isdb32_common(dbase32.isdb32_p)

    def test_isdb32_c(self):
        self.skip_if_no_c_ext()
        self.check_isdb32_common(dbase32.isdb32_c)

    def test_random_id(self):
        txt = dbase32.random_id()
        self.assertIsInstance(txt, str)
        self.assertEqual(len(txt), 24)
        data = dbase32.db32dec(txt)
        self.assertIsInstance(data, bytes)
        self.assertEqual(len(data), 15)
        self.assertEqual(dbase32.db32enc(data), txt)

        for size in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]:
            txt = dbase32.random_id(size)
            self.assertIsInstance(txt, str)
            self.assertEqual(len(txt), size * 8 // 5)
            data = dbase32.db32dec(txt)
            self.assertIsInstance(data, bytes)
            self.assertEqual(len(data), size)
            self.assertEqual(dbase32.db32enc(data), txt)

        # Sanity check on their randomness:
        count = 5000
        accum = set(dbase32.random_id() for i in range(count))
        self.assertEqual(len(accum), count)

