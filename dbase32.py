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

# DB32: Dmedia-Base32: non-standard 3-9, A-Y letters (sorted)
# [removes 0, 1, 2, Z]
DB32_START = 51
DB32_END = 89
DB32_FORWARD = '3456789ABCDEFGHIJKLMNOPQRSTUVWXY'
DB32_REVERSE = (
      0,  # 51 '3' [ 0]
      1,  # 52 '4' [ 1]
      2,  # 53 '5' [ 2]
      3,  # 54 '6' [ 3]
      4,  # 55 '7' [ 4]
      5,  # 56 '8' [ 5]
      6,  # 57 '9' [ 6]
    255,  # 58 ':' [ 7]
    255,  # 59 ';' [ 8]
    255,  # 60 '<' [ 9]
    255,  # 61 '=' [10]
    255,  # 62 '>' [11]
    255,  # 63 '?' [12]
    255,  # 64 '@' [13]
      7,  # 65 'A' [14]
      8,  # 66 'B' [15]
      9,  # 67 'C' [16]
     10,  # 68 'D' [17]
     11,  # 69 'E' [18]
     12,  # 70 'F' [19]
     13,  # 71 'G' [20]
     14,  # 72 'H' [21]
     15,  # 73 'I' [22]
     16,  # 74 'J' [23]
     17,  # 75 'K' [24]
     18,  # 76 'L' [25]
     19,  # 77 'M' [26]
     20,  # 78 'N' [27]
     21,  # 79 'O' [28]
     22,  # 80 'P' [29]
     23,  # 81 'Q' [30]
     24,  # 82 'R' [31]
     25,  # 83 'S' [32]
     26,  # 84 'T' [33]
     27,  # 85 'U' [34]
     28,  # 86 'V' [35]
     29,  # 87 'W' [36]
     30,  # 88 'X' [37]
     31,  # 89 'Y' [38]
)


def _encode_x_iter(data, x_forward):
    taxi = 0
    bits = 0
    for d in data:
        taxi = (taxi << 8) | d
        bits += 8
        while bits >= 5:
            bits -= 5
            yield x_forward[(taxi >> bits) & 31]
    assert bits == 0


def encode_x(data, x_forward):
    assert isinstance(data, bytes)
    if not (5 <= len(data) <= MAX_DATA):
        raise ValueError(
            'len(data) is {}, need 5 <= len(data) <= {}'.format(
                len(data), MAX_DATA
            )
        )
    if len(data) % 5 != 0:
        raise ValueError(
            'len(data) is {}, need len(data) % 5 == 0'.format(len(data))
        )
    return ''.join(_encode_x_iter(data, x_forward))


def _decode_x_iter(text, x_reverse, x_start, x_end):
    taxi = 0
    bits = 0
    for t in text:
        i = ord(t)
        if not (x_start <= i <= x_end):
            raise ValueError('invalid base32 letter: {}'.format(t))
        r = x_reverse[i - x_start]
        if r > 31:
            raise ValueError('invalid base32 letter: {}'.format(t))
        taxi = (taxi << 5) | r
        bits += 5
        while bits >= 8:
            bits -= 8
            yield (taxi >> bits) & 255
    assert bits == 0


def decode_x(text, x_reverse, x_start, x_end):
    assert isinstance(text, str)
    if not (8 <= len(text) <= MAX_TEXT):
        raise ValueError(
            'len(text) is {}, need 8 <= len(text) <= {}'.format(
                len(text), MAX_TEXT
            )
        )
    if len(text) % 8 != 0:
        raise ValueError(
            'len(text) is {}, need len(text) % 8 == 0'.format(len(text))
        )
    return bytes(_decode_x_iter(text, x_reverse, x_start, x_end))


def db32enc_p(data):
    return encode_x(data, DB32_FORWARD)


def db32dec_p(text):
    return decode_x(text, DB32_REVERSE, DB32_START, DB32_END)


try:
    from _dbase32 import db32enc, db32dec
except ImportError:
    pass

