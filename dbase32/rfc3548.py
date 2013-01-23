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
Validate encode_x(), decode_x() against known good RFC-3548 encode/decode.
"""

from . import encode_x, decode_x


__all__ = ('b32enc', 'b32dec')

# B32: RFC-3548: different binary vs encoded sort order (deal breaker!)
# [removes 0, 1, 8, 9]
B32_START = 50
B32_END = 90
B32_FORWARD = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
B32_REVERSE = (
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,
     26,  # '2' [50]
     27,  # '3' [51]
     28,  # '4' [52]
     29,  # '5' [53]
     30,  # '6' [54]
     31,  # '7' [55]
    255,  # '8' [56]
    255,  # '9' [57]
    255,  # ':' [58]
    255,  # ';' [59]
    255,  # '<' [60]
    255,  # '=' [61]
    255,  # '>' [62]
    255,  # '?' [63]
    255,  # '@' [64]
      0,  # 'A' [65]
      1,  # 'B' [66]
      2,  # 'C' [67]
      3,  # 'D' [68]
      4,  # 'E' [69]
      5,  # 'F' [70]
      6,  # 'G' [71]
      7,  # 'H' [72]
      8,  # 'I' [73]
      9,  # 'J' [74]
     10,  # 'K' [75]
     11,  # 'L' [76]
     12,  # 'M' [77]
     13,  # 'N' [78]
     14,  # 'O' [79]
     15,  # 'P' [80]
     16,  # 'Q' [81]
     17,  # 'R' [82]
     18,  # 'S' [83]
     19,  # 'T' [84]
     20,  # 'U' [85]
     21,  # 'V' [86]
     22,  # 'W' [87]
     23,  # 'X' [88]
     24,  # 'Y' [89]
     25,  # 'Z' [90]
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,
)


def b32enc(data):
    return encode_x(data, B32_FORWARD)


def b32dec(text):
    return decode_x(text, B32_REVERSE)

