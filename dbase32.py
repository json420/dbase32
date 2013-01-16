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


MAX_DATA = 60  # 480 bits
MAX_TEXT = MAX_DATA * 8 // 5

START = 51
END = 89

forward = '3456789ABCDEFGHIJKLMNOPQRSTUVWXY'

reverse = (
      0,  # 51 '3'
      1,  # 52 '4'
      2,  # 53 '5'
      3,  # 54 '6'
      4,  # 55 '7'
      5,  # 56 '8'
      6,  # 57 '9'
    255,  # 58 ':'
    255,  # 59 ';'
    255,  # 60 '<'
    255,  # 61 '='
    255,  # 62 '>'
    255,  # 63 '?'
    255,  # 64 '@'
      7,  # 65 'A'
      8,  # 66 'B'
      9,  # 67 'C'
     10,  # 68 'D'
     11,  # 69 'E'
     12,  # 70 'F'
     13,  # 71 'G'
     14,  # 72 'H'
     15,  # 73 'I'
     16,  # 74 'J'
     17,  # 75 'K'
     18,  # 76 'L'
     19,  # 77 'M'
     20,  # 78 'N'
     21,  # 79 'O'
     22,  # 80 'P'
     23,  # 81 'Q'
     24,  # 82 'R'
     25,  # 83 'S'
     26,  # 84 'T'
     27,  # 85 'U'
     28,  # 86 'V'
     29,  # 87 'W'
     30,  # 88 'X'
     31,  # 89 'Y'
)



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


def dec_iter(text, rmap, sne):
    (start, end) = sne
    taxi = 0
    bits = 0
    for t in text:
        i = ord(t)
        if not (start <= i <= end):
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
    if not (5 <= len(data) <= MAX_DATA):
        raise ValueError('need 5 <= len(data) <= {!r}'.format(MAX_DATA))
    if len(data) % 5 != 0:
        raise ValueError('len(data) % 5 != 0')
    return ''.join(enc_iter(data, fmap))


def dec(text, rmap=reverse, sne=(START, END)):
    assert isinstance(text, str)
    if not (8 <= len(text) <= MAX_TEXT):
        raise ValueError('need 8 <= len(text) <= {!r}'.format(MAX_TEXT))
    if len(text) % 8 != 0:
        raise ValueError('len(text) % 8 != 0')
    return bytes(dec_iter(text, rmap, sne))


