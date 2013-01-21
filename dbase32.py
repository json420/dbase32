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

__all__ = ('db32enc', 'db32dec')

MAX_BIN_LEN = 60  # 480 bits
MAX_TXT_LEN = 96

# B32: RFC-3548: different binary vs encoded sort order (deal breaker!)
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

# SB32: Sorted-Base32: standard RFC-3548 letters, but in sorted order
# [removes 0, 1, 8, 9]
SB32_START = 50
SB32_END = 90
SB32_FORWARD = '234567ABCDEFGHIJKLMNOPQRSTUVWXYZ'
SB32_REVERSE = (
      0,  # 50 '2' [ 0]
      1,  # 51 '3' [ 1]
      2,  # 52 '4' [ 2]
      3,  # 53 '5' [ 3]
      4,  # 54 '6' [ 4]
      5,  # 55 '7' [ 5]
    255,  # 56 '8' [ 6]
    255,  # 57 '9' [ 7]
    255,  # 58 ':' [ 8]
    255,  # 59 ';' [ 9]
    255,  # 60 '<' [10]
    255,  # 61 '=' [11]
    255,  # 62 '>' [12]
    255,  # 63 '?' [13]
    255,  # 64 '@' [14]
      6,  # 65 'A' [15]
      7,  # 66 'B' [16]
      8,  # 67 'C' [17]
      9,  # 68 'D' [18]
     10,  # 69 'E' [19]
     11,  # 70 'F' [20]
     12,  # 71 'G' [21]
     13,  # 72 'H' [22]
     14,  # 73 'I' [23]
     15,  # 74 'J' [24]
     16,  # 75 'K' [25]
     17,  # 76 'L' [26]
     18,  # 77 'M' [27]
     19,  # 78 'N' [28]
     20,  # 79 'O' [29]
     21,  # 80 'P' [30]
     22,  # 81 'Q' [31]
     23,  # 82 'R' [32]
     24,  # 83 'S' [33]
     25,  # 84 'T' [34]
     26,  # 85 'U' [35]
     27,  # 86 'V' [36]
     28,  # 87 'W' [37]
     29,  # 88 'X' [38]
     30,  # 89 'Y' [39]
     31,  # 90 'Z' [40]
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
    offset = 0
    for i in range(len(data) // 5):
        taxi = data[offset]
        taxi = (taxi << 8) | data[offset + 1]
        taxi = (taxi << 8) | data[offset + 2]
        taxi = (taxi << 8) | data[offset + 3]
        taxi = (taxi << 8) | data[offset + 4]
        yield x_forward[(taxi >> 35) & 31]
        yield x_forward[(taxi >> 30) & 31]
        yield x_forward[(taxi >> 25) & 31]
        yield x_forward[(taxi >> 20) & 31]
        yield x_forward[(taxi >> 15) & 31]
        yield x_forward[(taxi >> 10) & 31]
        yield x_forward[(taxi >>  5) & 31]
        yield x_forward[taxi & 31]
        offset += 5


def encode_x(data, x_forward):
    assert isinstance(data, bytes)
    if not (5 <= len(data) <= MAX_BIN_LEN):
        raise ValueError(
            'len(data) is {}, need 5 <= len(data) <= {}'.format(
                len(data), MAX_BIN_LEN
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
    if not (8 <= len(text) <= MAX_TXT_LEN):
        raise ValueError(
            'len(text) is {}, need 8 <= len(text) <= {}'.format(
                len(text), MAX_TXT_LEN
            )
        )
    if len(text) % 8 != 0:
        raise ValueError(
            'len(text) is {}, need len(text) % 8 == 0'.format(len(text))
        )
    return bytes(_decode_x_iter(text, x_reverse, x_start, x_end))


def db32enc_p(data):
    """
    Encode *data* into a D-Base32 string.

    For exmple:

    >>> db32enc_p(b'binary foo')
    'FCNPVRELI7J9FUUI'

    """
    return encode_x(data, DB32_FORWARD)


def db32dec_p(text):
    """
    Decode D-Base32 encoded *text*.

    For exmple:

    >>> db32dec_p('FCNPVRELI7J9FUUI')
    b'binary foo'

    """
    return decode_x(text, DB32_REVERSE, DB32_START, DB32_END)


def sb32enc(data):
    return encode_x(data, SB32_FORWARD)

def sb32dec(text):
    return decode_x(text, SB32_REVERSE, SB32_START, SB32_END)

def b32enc(data):
    return encode_x(data, B32_FORWARD)

def b32dec(text):
    return decode_x(text, B32_REVERSE, B32_START, B32_END)


try:
    from _dbase32 import db32enc_c, db32dec_c
    db32enc = db32enc_c
    db32dec = db32dec_c
except ImportError:
    db32enc = db32enc_p
    db32dec = db32dec_p

