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


static const uint8_t forward[32] = "3456789ABCDEFGHIJKLMNOPQRSTUVWXY";

static const uint8_t reverse[39] = {
      0,  // 51 '3'
      1,  // 52 '4'
      2,  // 53 '5'
      3,  // 54 '6'
      4,  // 55 '7'
      5,  // 56 '8'
      6,  // 57 '9'
    255,  // 58 ':'
    255,  // 59 ';'
    255,  // 60 '<'
    255,  // 61 '='
    255,  // 62 '>'
    255,  // 63 '?'
    255,  // 64 '@'
      7,  // 65 'A'
      8,  // 66 'B'
      9,  // 67 'C'
     10,  // 68 'D'
     11,  // 69 'E'
     12,  // 70 'F'
     13,  // 71 'G'
     14,  // 72 'H'
     15,  // 73 'I'
     16,  // 74 'J'
     17,  // 75 'K'
     18,  // 76 'L'
     19,  // 77 'M'
     20,  // 78 'N'
     21,  // 79 'O'
     22,  // 80 'P'
     23,  // 81 'Q'
     24,  // 82 'R'
     25,  // 83 'S'
     26,  // 84 'T'
     27,  // 85 'U'
     28,  // 86 'V'
     29,  // 87 'W'
     30,  // 88 'X'
     31,  // 89 'Y'
};

