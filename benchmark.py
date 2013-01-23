#!/usr/bin/python3

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
Benchmark the db32enc(), db32dec() C implementation.
"""

import timeit

setup = """
import os
from base64 import b64encode, b64decode

from dbase32 import db32enc, db32dec


data = os.urandom(60)
text_b64 = b64encode(data)
text_db32 = db32enc(data)

assert b64decode(text_b64) == data
assert db32dec(text_db32) == data
"""

N = 2500 * 1000

def run(statement):
    t = timeit.Timer(statement, setup)
    elapsed = t.timeit(N)
    rate = int(N / elapsed)
    print('{:>14,}: {}'.format(rate, statement))


print('')

print('Encodes/second:')
run('b64encode(data)')
run('db32enc(data)')
print('')

print('Decodes/second:')
run('b64decode(text_b64)')
run('db32dec(text_db32)')
print('')
