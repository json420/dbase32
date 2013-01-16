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
from base64 import b32encode, b32decode

from dbase32 import enc, dec, db32enc

data15 = os.urandom(15)
data30 = os.urandom(30)

b32_15 = b32encode(data15)
b32_30 = b32encode(data30)

db32_15 = enc(data15)
db32_30 = enc(data30)
"""

N = 50 * 1000

def run(statement):
    t = timeit.Timer(statement, setup)
    elapsed = t.timeit(N)
    rate = int(N / elapsed)
    print('{:>10,}: {}'.format(rate, statement))


print('Executions per second:')

run('b32encode(data15)')
run('b32encode(data30)')

run('enc(data15)')
run('enc(data30)')

run('db32enc(data15)')
run('db32enc(data30)')

run('b32decode(b32_15)')
run('b32decode(b32_30)')

run('dec(db32_15)')
run('dec(db32_30)')

