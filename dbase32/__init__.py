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

from os import urandom


__version__ = '0.1.0'
__all__ = ('db32enc', 'db32dec', 'isdb32', 'check_db32', 'random_id')

MAX_BIN_LEN = 60  # 480 bits
MAX_TXT_LEN = 96

RANDOM_BITS = 120
RANDOM_BYTES = 15
RANDOM_B32LEN = 24

# DB32: Dmedia-Base32: non-standard 3-9, A-Y letters (sorted)
# [removes 0, 1, 2, Z]
DB32_START = 51
DB32_END = 89
DB32_FORWARD = '3456789ABCDEFGHIJKLMNOPQRSTUVWXY'
DB32_REVERSE = (
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,
      0,  # '3' [51]
      1,  # '4' [52]
      2,  # '5' [53]
      3,  # '6' [54]
      4,  # '7' [55]
      5,  # '8' [56]
      6,  # '9' [57]
    255,  # ':' [58]
    255,  # ';' [59]
    255,  # '<' [60]
    255,  # '=' [61]
    255,  # '>' [62]
    255,  # '?' [63]
    255,  # '@' [64]
      7,  # 'A' [65]
      8,  # 'B' [66]
      9,  # 'C' [67]
     10,  # 'D' [68]
     11,  # 'E' [69]
     12,  # 'F' [70]
     13,  # 'G' [71]
     14,  # 'H' [72]
     15,  # 'I' [73]
     16,  # 'J' [74]
     17,  # 'K' [75]
     18,  # 'L' [76]
     19,  # 'M' [77]
     20,  # 'N' [78]
     21,  # 'O' [79]
     22,  # 'P' [80]
     23,  # 'Q' [81]
     24,  # 'R' [82]
     25,  # 'S' [83]
     26,  # 'T' [84]
     27,  # 'U' [85]
     28,  # 'V' [86]
     29,  # 'W' [87]
     30,  # 'X' [88]
     31,  # 'Y' [89]
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,
)

# Equivalent of filestore.B32ALPHABET:
DB32ALPHABET = frozenset(DB32_FORWARD)


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
    if not isinstance(data, bytes):
        raise TypeError("'str' does not support the buffer interface")
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


def _decode_x_iter(text, x_reverse):
    taxi = 0
    bits = 0
    for t in text:
        r = x_reverse[ord(t)]
        if r > 31:
            raise ValueError('invalid D-Base32 letter: {}'.format(t))
        taxi = (taxi << 5) | r
        bits += 5
        while bits >= 8:
            bits -= 8
            yield (taxi >> bits) & 255
    assert bits == 0


def decode_x(text, x_reverse):
    if not isinstance(text, str):
        raise TypeError('must be str, not bytes')
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
    return bytes(_decode_x_iter(text, x_reverse))


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
    return decode_x(text, DB32_REVERSE)


def isdb32_p(text):
    if not isinstance(text, str):
        raise TypeError('must be str, not bytes')
    if not (8 <= len(text) <= MAX_TXT_LEN):
        return False
    if len(text) % 8 != 0:
        return False
    return DB32ALPHABET.issuperset(text)


def check_db32_p(text):
    if not isinstance(text, str):
        raise TypeError('must be str, not bytes')
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
    if not DB32ALPHABET.issuperset(text):
        for t in text:
            if t not in DB32ALPHABET:    
                raise ValueError('invalid D-Base32 letter: {}'.format(t))


try:
    from _dbase32 import db32enc_c, db32dec_c, isdb32_c, check_db32_c
    db32enc = db32enc_c
    db32dec = db32dec_c
    isdb32 = isdb32_c
    check_db32 = check_db32_c
except ImportError:
    db32enc = db32enc_p
    db32dec = db32dec_p
    isdb32 = isdb32_p
    check_db32 = check_db32_p


def random_id(numbytes=RANDOM_BYTES):
    """
    Returns a 120-bit DBase32-encoded random ID.

    The ID will be 24-characters long, URL and filesystem safe.
    """
    return db32enc(urandom(numbytes))

