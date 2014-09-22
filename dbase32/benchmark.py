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
from dbase32 import _dbase32, _dbase32py

text_db32 = {!r}
data = _dbase32.db32dec(text_db32)
text_b64 = base64.b64encode(data)
not_db32 = text_db32[:-1] + 'Z'

assert base64.b64decode(text_b64) == data
assert _dbase32.db32dec(text_db32) == data

assert _dbase32py.isdb32(text_db32) is True
assert _dbase32.isdb32(text_db32) is True
assert _dbase32py.isdb32(not_db32) is False
assert _dbase32.isdb32(not_db32) is False

def timing_test(text):
    try:
        _dbase32.check_db32(text)
    except ValueError:
        pass
"""


def run_benchmark(numbytes=30):
    text_db32 = dbase32.random_id(numbytes)
    setup = SETUP.format(text_db32)

    def run(statement, k=750):
        count = k * 1000
        t = timeit.Timer(statement, setup)
        elapsed = t.timeit(count)
        rate = int(count / elapsed)
        return '{:>12,}: {}'.format(rate, statement)

    yield 'dbase32: {}'.format(dbase32.__version__)
    yield 'Python: {}, {}, {} ({} {})'.format(
        platform.python_version(),
        platform.machine(),
        platform.system(),
        platform.dist()[0],
        platform.dist()[1],
    )
    yield 'data size: {} bytes'.format(numbytes)

    yield 'Encodes/second:'
    yield run('base64.b64encode(data)')
    yield run('_dbase32.db32enc(data)')
    yield run('_dbase32py.db32enc(data)', 25)

    yield 'Decodes/second:'
    yield run('base64.b64decode(text_b64)')
    yield run('_dbase32.db32dec(text_db32)')
    yield run('_dbase32py.db32dec(text_db32)', 25)

    yield 'Validations/second:'
    yield run('_dbase32.isdb32(text_db32)')
    yield run('_dbase32py.isdb32(text_db32)', 100)
    yield run('_dbase32.check_db32(text_db32)')
    yield run('_dbase32py.check_db32(text_db32)', 100)

    yield 'Random IDs/second:'
    yield run('os.urandom(15)', 100)
    yield run('_dbase32.random_id(15)', 100)
    yield run('_dbase32.time_id()', 100)

    yield 'Timing attack test:'
    for index in (0, 8, 16):
        letters = ['A' for i in range(24)]
        letters[index] = 'a'
        text = ''.join(letters)
        yield run('timing_test({!r})'.format(text))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bytes', metavar='N', type=int,
        default=30,
        help='length of binary ID in bytes',
    )
    args = parser.parse_args()
    for line in run_benchmark(args.bytes):
        print(line)

