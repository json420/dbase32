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
Unit tests for `dbase32.misc` module.
"""

from unittest import TestCase

from dbase32.misc import TYPE_ERROR
from dbase32 import misc


class TestFunctions(TestCase):
    def test_gen_forward(self):
        with self.assertRaises(TypeError) as cm:
            misc.gen_forward(b'0123')
        self.assertEqual(
            str(cm.exception),
            TYPE_ERROR.format('remove', str, bytes, b'0123')
        )

        with self.assertRaises(ValueError) as cm:
            misc.gen_forward('ABC')
        self.assertEqual(
            str(cm.exception),
            "len(remove) != 4: [3] 'ABC'"
        )

        with self.assertRaises(ValueError) as cm:
            misc.gen_forward('ABCDE')
        self.assertEqual(
            str(cm.exception),
            "len(remove) != 4: [5] 'ABCDE'"
        )

        with self.assertRaises(ValueError) as cm:
            misc.gen_forward('ABCA')
        self.assertEqual(
            str(cm.exception),
            "len(set(remove)) != 4: [3] 'ABCA'"
        )

        with self.assertRaises(ValueError) as cm:
            misc.gen_forward('012z')
        self.assertEqual(
            str(cm.exception),
            "remove: '012z' not a subset of '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'"
        )

        self.assertEqual(
            misc.gen_forward('4IOU'),
            '012356789ABCDEFGHJKLMNPQRSTVWXYZ'
        )
        self.assertEqual(
            misc.gen_forward('PONM'),
            '0123456789ABCDEFGHIJKLQRSTUVWXYZ'
        )
        self.assertEqual(
            misc.gen_forward('8967'),
            '012345ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        )

    def test_check_forward(self):
        bad = b'0123456789ABCDEFGHIJKLMNOPQRSTUV'
        with self.assertRaises(TypeError) as cm:
            misc.check_forward(bad)
        self.assertEqual(
            str(cm.exception),
            TYPE_ERROR.format('forward', str, bytes, bad)
        )

        bad = '3456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        with self.assertRaises(ValueError) as cm:
            misc.check_forward(bad)
        self.assertEqual(
            str(cm.exception),
            'len(forward) != 32: [33] {!r}'.format(bad)
        )

        bad = '56789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        with self.assertRaises(ValueError) as cm:
            misc.check_forward(bad)
        self.assertEqual(
            str(cm.exception),
            'len(forward) != 32: [31] {!r}'.format(bad)
        )

        bad = '45678ZABCDEFGHIJKLMNOPQRSTUVWXYZ'
        with self.assertRaises(ValueError) as cm:
            misc.check_forward(bad)
        self.assertEqual(
            str(cm.exception),
            'len(set(forward)) != 32: [31] {!r}'.format(bad)
        )

        bad = '456789abcDEFGHIJKLMNOPQRSTUVWXYZ'
        with self.assertRaises(ValueError) as cm:
            misc.check_forward(bad)
        self.assertEqual(
            str(cm.exception),
            'forward: {!r} not a subset of {!r}'.format(bad, misc.POSSIBLE)
        )

        good = '012356789ABCDEFGHJKLMNPQRSTVWXYZ'
        self.assertIs(misc.check_forward(good), good)
