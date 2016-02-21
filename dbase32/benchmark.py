#!/usr/bin/python3

# dbase32: base32-encoding with a sorted-order alphabet (for databases)
# Copyright (C) 2013-2016 Novacut Inc
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
gc.enable()

import os
from os import urandom
from base64 import b64encode, b64decode

from dbase32 import (
    db32dec,
    db32enc,
    isdb32,
    check_db32,
    random_id,
    time_id,
    db32_relpath,
    db32_abspath,
)

text = {!r}
parentdir = {!r}

data = db32dec(text)
text_b64 = b64encode(data)
not_db32 = text[:-1] + 'Z'

assert b64decode(text_b64) == data
assert db32dec(text) == data

assert isdb32(text) is True
assert isdb32(not_db32) is False
"""


def run_benchmark(numbytes=30):
    text = dbase32.random_id(numbytes)
    parentdir = '/tmp/' + dbase32.random_id()
    setup = SETUP.format(text, parentdir)

    def run(statement, k=1000):
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

    yield 'Encodes/second compared to base64.b64encode():'
    yield run('b64encode(data)')
    yield run('db32enc(data)')

    yield 'Decodes/second compared to base64.b64decode():'
    yield run('b64decode(text_b64)')
    yield run('db32dec(text)')

    yield 'Validations/second:'
    yield run('isdb32(text)')
    yield run('check_db32(text)')

    yield 'Validated Path Constructions/second:'
    yield run('db32_relpath(text)')
    yield run('db32_abspath(parentdir, text)')

    yield 'Random IDs/second compared to os.urandom():'
    yield run('urandom(15)', 200)
    yield run('random_id(15)', 200)
    yield run('time_id()', 200)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bytes', metavar='N', type=int,
        default=30,
        help='length of binary ID in bytes',
    )
    args = parser.parse_args()
    for line in run_benchmark(args.bytes):
        print(line)

