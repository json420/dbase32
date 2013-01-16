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
`dbase32` - base32-encoding with a sorted-order alphabet (for databases).
"""

__version__ = '0.1.0'


MIN_DATA = 5  # 40 bits
MAX_DATA = 60  # 480 bits

MIN_TEXT = MIN_DATA * 8 // 5
MAX_TEXT = MAX_DATA * 8 // 5


forward = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'

reverse = (
      0,  # 50 '2'
      1,  # 51 '3'
      2,  # 52 '4'
      3,  # 53 '5'
      4,  # 54 '6'
      5,  # 55 '7'
      6,  # 56 '8'
      7,  # 57 '9'
    255,  # 58 ':'
    255,  # 59 ';'
    255,  # 60 '<'
    255,  # 61 '='
    255,  # 62 '>'
    255,  # 63 '?'
    255,  # 64 '@'
      8,  # 65 'A'
      9,  # 66 'B'
     10,  # 67 'C'
     11,  # 68 'D'
     12,  # 69 'E'
     13,  # 70 'F'
     14,  # 71 'G'
     15,  # 72 'H'
    255,  # 73 'I'
     16,  # 74 'J'
     17,  # 75 'K'
     18,  # 76 'L'
     19,  # 77 'M'
     20,  # 78 'N'
    255,  # 79 'O'
     21,  # 80 'P'
     22,  # 81 'Q'
     23,  # 82 'R'
     24,  # 83 'S'
     25,  # 84 'T'
     26,  # 85 'U'
     27,  # 86 'V'
     28,  # 87 'W'
     29,  # 88 'X'
     30,  # 89 'Y'
     31,  # 90 'Z'
)

start = 50
stop = 91


def enc_iter(data, fmap):
    taxi = 0
    bits = 0
    for d in data:
        taxi = (taxi << 8) | d
        bits += 8
        while bits >= 5:
            bits -= 5
            yield fmap[(taxi >> bits) & 31]
    assert bits == 0


def dec_iter(text, rmap):
    taxi = 0
    bits = 0
    for t in text:
        i = ord(t)
        if not (start <= i < stop):
            raise ValueError('invalid base32 letter: {!r}'.format(t))
        r = rmap[i - start]
        if r > 31:
            raise ValueError('invalid base32 letter: {!r}'.format(t))
        taxi = (taxi << 5) | r
        bits += 5
        while bits >= 8:
            bits -= 8
            yield (taxi >> bits) & 255
    assert bits == 0


def enc(data, fmap=forward):
    assert isinstance(data, bytes)
    if not (MIN_DATA <= len(data) <= MAX_DATA):
        raise ValueError(
            'need {!r} <= len(data) <= {!r}'.format(MIN_DATA, MAX_DATA)
        )
    if len(data) % 5 != 0:
        raise ValueError('len(data) % 5 != 0')
    return ''.join(enc_iter(data, fmap))


def dec(text, rmap=reverse):
    assert isinstance(text, str)
    if not (MIN_TEXT <= len(text) <= MAX_TEXT):
        raise ValueError(
            'need {!r} <= len(text) <= {!r}'.format(MIN_TEXT, MAX_TEXT)
        )
    if len(text) % 8 != 0:
        raise ValueError('len(text) % 8 != 0')
    return bytes(dec_iter(text, rmap))


