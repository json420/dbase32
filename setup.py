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
from venv import EnvBuilder
from os import path
import tempfile
import shutil
from subprocess import check_call, call

import dbase32
import dbase32test


class TestEnvBuilder(EnvBuilder):
    def __init__(self):
        self.tmpdir = tempfile.mkdtemp(prefix='venv.')
        super().__init__(system_site_packages=True, symlinks=True)
        self.create(path.join(self.tmpdir, 'tests'))

    def __del__(self):
        if path.isdir(self.tmpdir):
            print('Removing {!r}'.format(self.tmpdir))
            shutil.rmtree(self.tmpdir)

    def post_setup(self, context):
        setup = path.abspath(__file__)
        check_call([context.env_exe, setup, 'install'])
        #run_tests = path.join(context.env_dir, 'local', 'bin', 'dbase32-run-tests')
        #assert path.isfile(run_tests)
        self.run_tests_cmd = [context.env_exe, '-m', 'dbase32test']

    def run_tests(self):
        return call(self.run_tests_cmd) == 0


class Test(Command):
    description = 'run unit tests and doc tests'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # First run the tests in the source tree
        if not dbase32test.run_tests():
            raise SystemExit('Tests failed in source tree!')

        # Now run the tests in a virtual environment:
        testenv = TestEnvBuilder()
        if not testenv.run_tests():
            raise SystemExit('Tests failed in virtual environment!')


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
    py_modules=['dbase32test'],
    ext_modules=[_dbase32],
    cmdclass={'test': Test},
)
