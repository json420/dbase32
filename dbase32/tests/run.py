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
Run `dbase32` unit tests.
"""

import sys
from os import path
from unittest import TestLoader, TextTestRunner
from doctest import DocTestSuite

import dbase32

pynames = (
    'dbase32',
    'dbase32.fallback',
    'dbase32.rfc3548',
    'dbase32.gen',
    'dbase32.tests',
    'dbase32.tests.test_fallback',
    'dbase32.tests.test_rfc3548',
    'dbase32.tests.test_gen',
)


def run_tests():
    # Add unit-tests:
    loader = TestLoader()
    suite = loader.loadTestsFromNames(pynames)

    # Add doc-tests:
    for name in pynames:
        suite.addTest(DocTestSuite(name))

    # Run the tests:
    runner = TextTestRunner(verbosity=2)
    result = runner.run(suite)
    success =  result.wasSuccessful()
    print(
        'dbase32: {!r}'.format(path.abspath(dbase32.__file__)),
        file=sys.stderr
    )
    if success:
        print('Tests passed.', file=sys.stderr)
    else:
        print('Tests FAILED!', file=sys.stderr)
    return success


if __name__ == '__main__':
    if not run_tests():
        raise SystemExit('2')

