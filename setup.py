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

"""
Install `dbase32`.
"""

import sys
if sys.version_info < (3, 3):
    sys.exit('dbase32 requires Python 3.3 or newer')

from distutils.core import setup, Extension
from distutils.cmd import Command

import dbase32
from dbase32.tests.run import run_tests


class Test(Command):
    description = 'run unit tests and doc tests'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if not run_tests():
            raise SystemExit('2')


_dbase32 = Extension('_dbase32', sources=['_dbase32.c'],
    #extra_compile_args=['-O3']
)

setup(
    name='dbase32',
    description='base32-encoding with a sorted-order alphabet',
    url='https://launchpad.net/dbase32',
    version=dbase32.__version__,
    author='Jason Gerard DeRose',
    author_email='jderose@novacut.com',
    license='LGPLv3+',
    packages=[
        'dbase32',
        'dbase32.tests',
    ],
    ext_modules=[_dbase32],
    cmdclass={'test': Test},
)
