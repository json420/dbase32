#!/usr/bin/env python3

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

import timeit

setup = """

import os
from base64 import b32encode, b32decode, b64encode, b64decode

from dbase32 import db32enc_p, db32enc_c, db32dec_p, db32dec_c

data = os.urandom(60)
text_b32 = b32encode(data)
text_b64 = b64encode(data)
text_db32 = db32enc_p(data)

assert b32decode(text_b32) == data
assert b64decode(text_b64) == data
assert db32dec_p(text_db32) == data
assert db32dec_c(text_db32) == data
"""

def run(statement, slow=False):
    n = 50 * 1000 if slow else 2500 * 1000
    t = timeit.Timer(statement, setup)
    elapsed = t.timeit(n)
    rate = int(n / elapsed)
    print('{:>14,}: {}'.format(rate, statement))


print('')

print('Encodes/second:')
run('b32encode(data)', slow=True)
run('db32enc_p(data)', slow=True)
run('b64encode(data)')
run('db32enc_c(data)')
print('')

print('Decodes/second:')
run('b32decode(text_b32)', slow=True)
run('db32dec_p(text_db32)', slow=True)
run('b64decode(text_b64)')
run('db32dec_c(text_db32)')
print('')
