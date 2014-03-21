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
Install `dbase32`.
"""

import sys
if sys.version_info < (3, 3):
    sys.exit('ERROR: dbase32 requires Python 3.3 or newer')

import os
from os import path
import subprocess
from distutils.core import setup, Extension
from distutils.cmd import Command

import dbase32
from dbase32.tests.run import run_tests


def run_sphinx_doctest():
    sphinx_build = '/usr/share/sphinx/scripts/python3/sphinx-build'
    if not os.access(sphinx_build, os.R_OK | os.X_OK):
        print('warning, cannot read and execute: {!r}'.format(sphinx_build))
        return
    tree = path.dirname(path.abspath(__file__))
    doc = path.join(tree, 'doc')
    doctest = path.join(tree, 'doc', '_build', 'doctest')
    cmd = [sys.executable, sphinx_build, '-EW', '-b', 'doctest', doc, doctest]
    subprocess.check_call(cmd)


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
        run_sphinx_doctest()


class Benchmark(Command):
    description = 'run dbase32 benchmark'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from dbase32.benchmark import run_benchmark
        for line in run_benchmark():
            print(line)


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
    cmdclass={
        'test': Test,
        'benchmark': Benchmark,
    },
)
