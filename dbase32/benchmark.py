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
import platform
import argparse

import dbase32


SETUP = """
import os
import base64
import _dbase32
from dbase32 import fallback

text_db32 = {!r}
data = _dbase32.db32dec(text_db32)
text_b64 = base64.b64encode(data)
not_db32 = text_db32[:-1] + 'Z'

assert base64.b64decode(text_b64) == data
assert _dbase32.db32dec(text_db32) == data

assert fallback.isdb32(text_db32) is True
assert _dbase32.isdb32(text_db32) is True
assert fallback.isdb32(not_db32) is False
assert _dbase32.isdb32(not_db32) is False
"""


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bytes', metavar='N', type=int,
        default=60,
        help='length of binary ID in bytes',
    )
    args = parser.parse_args()

    text_db32 = dbase32.random_id(args.bytes)
    setup = SETUP.format(text_db32)


    def run(statement, k=2500):
        count = k * 1000
        t = timeit.Timer(statement, setup)
        elapsed = t.timeit(count)
        rate = int(count / elapsed)
        print('{:>14,}: {}'.format(rate, statement))


    print('dbase32: {}'.format(dbase32.__version__))
    print('Python: {}, {}, {} ({} {})'.format(
            platform.python_version(),
            platform.machine(),
            platform.system(),
            platform.dist()[0],
            platform.dist()[1],
        )
    )
    print('data size: {} bytes'.format(args.bytes))
    print('')

    print('Encodes/second:')
    run('base64.b64encode(data)')
    run('_dbase32.db32enc(data)')
    run('fallback.db32enc(data)', 25)

    print('Decodes/second:')
    run('base64.b64decode(text_b64)')
    run('_dbase32.db32dec(text_db32)')
    run('fallback.db32dec(text_db32)', 25)

    print('Validations/second:')
    run('_dbase32.isdb32(text_db32)')
    run('fallback.isdb32(text_db32)', 250)
    run('_dbase32.check_db32(text_db32)')
    run('fallback.check_db32(text_db32)', 250)

    print('Random IDs/second:')
    run('os.urandom(15)', 300)
    run('_dbase32.random_id(15)', 300)
    run('fallback.random_id(15)', 150)

    print('')

