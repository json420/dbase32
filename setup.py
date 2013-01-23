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
from unittest import TestLoader, TextTestRunner
from doctest import DocTestSuite
from venv import EnvBuilder
from os import path
import tempfile
import shutil
from subprocess import check_call, call

import dbase32


def run(step, location, callback, *args):
    print('')
    print('*' * 80)
    print('*  ({}) running tests in {}...'.format(step, location))
    print('*' * 80)
    ret = callback(*args)
    print('*' * 80)
    print('')
    return ret


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
        run_tests = path.join(context.env_dir, 'local', 'bin', 'dbase32-run-tests')
        assert path.isfile(run_tests)
        self.run_tests_cmd = [context.env_exe, run_tests]

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
        pynames = [
            'dbase32',
            'dbase32.rfc3548',
            'dbase32.misc',
            'dbase32.tests',
            'dbase32.tests.test_rfc3548',
            'dbase32.tests.test_misc',
        ]
        loader = TestLoader()
        suite = loader.loadTestsFromNames(pynames)
        for name in pynames:
            suite.addTest(DocTestSuite(name))
        runner = TextTestRunner(verbosity=2)
        result = run(1, 'source tree', runner.run, suite)
        if not result.wasSuccessful():
            raise SystemExit('Tests failed in source tree!')

        # Now run the tests in a virtual environment:
        testenv = TestEnvBuilder()
        if not run(2, 'virtual environment', testenv.run_tests):
            raise SystemExit('Tests failed in virtual environment!')


_dbase32 = Extension('_dbase32', sources=['_dbase32.c'],
    extra_compile_args=['-O3']
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
    scripts=[
        'dbase32-gen-tables',
        'dbase32-benchmark',
        'dbase32-run-tests',
    ],
    ext_modules=[_dbase32],
    cmdclass={'test': Test},
)
