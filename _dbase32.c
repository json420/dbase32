/*
dbase32: base32-encoding with a sorted-order alphabet (for databases)
Copyright (C) 2013 Novacut Inc

This file is part of `dbase32`.

`dbase32` is free software: you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

`dbase32` is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
details.

You should have received a copy of the GNU Lesser General Public License along
with `dbase32`.  If not, see <http://www.gnu.org/licenses/>.

Authors:
    Jason Gerard DeRose <jderose@novacut.com>
*/


static const uint8_t forward[32] = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ";

static const uint8_t reverse[41] = {
      0,  // 50 '2'
      1,  // 51 '3'
      2,  // 52 '4'
      3,  // 53 '5'
      4,  // 54 '6'
      5,  // 55 '7'
      6,  // 56 '8'
      7,  // 57 '9'
    255,  // 58 ':'
    255,  // 59 ';'
    255,  // 60 '<'
    255,  // 61 '='
    255,  // 62 '>'
    255,  // 63 '?'
    255,  // 64 '@'
      8,  // 65 'A'
      9,  // 66 'B'
     10,  // 67 'C'
     11,  // 68 'D'
     12,  // 69 'E'
     13,  // 70 'F'
     14,  // 71 'G'
     15,  // 72 'H'
    255,  // 73 'I'
     16,  // 74 'J'
     17,  // 75 'K'
     18,  // 76 'L'
     19,  // 77 'M'
     20,  // 78 'N'
    255,  // 79 'O'
     21,  // 80 'P'
     22,  // 81 'Q'
     23,  // 82 'R'
     24,  // 83 'S'
     25,  // 84 'T'
     26,  // 85 'U'
     27,  // 86 'V'
     28,  // 87 'W'
     29,  // 88 'X'
     30,  // 89 'Y'
     31,  // 90 'Z'
};
