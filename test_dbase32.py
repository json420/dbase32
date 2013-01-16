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

import dbase32


possible = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
assert ''.join(sorted(set(possible))) == possible


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

    def test_start_stop(self):
        self.assertEqual(dbase32.start, ord(dbase32.alphabet[0]))
        self.assertEqual(dbase32.stop, ord(dbase32.alphabet[-1]) + 1)
        self.assertEqual(dbase32.stop - dbase32.start, len(dbase32.r_alphabet))

