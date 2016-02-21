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
Install `dbase32`.
"""

import sys
if sys.version_info < (3, 4):
    sys.exit('ERROR: dbase32 requires Python 3.4 or newer')

import os
from os import path
import platform
import subprocess
from distutils.core import setup, Extension
from distutils.cmd import Command

import dbase32
from dbase32.tests.run import run_tests


TREE = path.dirname(path.abspath(__file__))
with open(path.join(TREE, 'README'), 'r') as fp:
    LONG_DESCRIPTION = fp.read()


def run_under_same_interpreter(opname, script, args):
    print('\n** running: {}...'.format(script), file=sys.stderr)
    if not os.access(script, os.R_OK | os.X_OK):
        print('ERROR: cannot read and execute: {!r}'.format(script),
            file=sys.stderr
        )
        print('Consider running `setup.py test --skip-{}`'.format(opname),
            file=sys.stderr
        )
        sys.exit(3)
    cmd = [sys.executable, script] + args
    print('check_call:', cmd, file=sys.stderr)
    subprocess.check_call(cmd)
    print('** PASSED: {}\n'.format(script), file=sys.stderr)


def run_sphinx_doctest():
    script = '/usr/share/sphinx/scripts/python3/sphinx-build'
    doc = path.join(TREE, 'doc')
    doctest = path.join(TREE, 'doc', '_build', 'doctest')
    args = ['-EW', '-b', 'doctest', doc, doctest]
    run_under_same_interpreter('sphinx', script, args)


def run_pyflakes3():
    script = '/usr/bin/pyflakes3'
    names = [
        'dbase32',
        'setup.py',
    ]
    args = [path.join(TREE, name) for name in names]
    run_under_same_interpreter('flakes', script, args)


class Test(Command):
    description = 'run unit tests and doctests'

    user_options = [
        ('skip-sphinx', None, 'do not run Sphinx doctests'),
        ('skip-flakes', None, 'do not run pyflakes static checks'),
    ]

    def initialize_options(self):
        self.skip_sphinx = 0
        self.skip_flakes = 0

    def finalize_options(self):
        pass

    def run(self):
        if not run_tests():
            sys.exit(2)
        if not self.skip_sphinx:
            run_sphinx_doctest()
        if not self.skip_flakes:
            run_pyflakes3()


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


ext_kw = {
    'sources': ['dbase32/_dbase32.c'],
    'extra_compile_args': [
        '-std=gnu11',  # Default in gcc 5.0
        '-Werror',  # Make all warnings into errors
        '-pedantic-errors',
        '-Wsign-compare',
        '-Wsign-conversion',
    ],
}
if os.environ.get('DBASE32_INSTRUMENT_BUILD') == 'true':
    ext_kw['extra_compile_args'].append('-fsanitize=address')
    ext_kw['libraries'] = ['asan']
    if platform.dist()[1] >= '15.04':
        ext_kw['extra_compile_args'].extend([
            '-fsanitize=undefined',
            '-fsanitize=shift',
            '-fsanitize=integer-divide-by-zero',
            '-fsanitize=unreachable',
            '-fsanitize=vla-bound',
            '-fsanitize=null',
            '-fsanitize=return',
            '-fsanitize=signed-integer-overflow',
        ])
        ext_kw['libraries'].append('ubsan')


setup(
    name='dbase32',
    description='A base32 encoding with a sorted-order alphabet',
    long_description=LONG_DESCRIPTION,
    url='https://launchpad.net/dbase32',
    version=dbase32.__version__,
    author='Jason Gerard DeRose',
    author_email='jderose@novacut.com',
    license='LGPLv3+',
    platforms=['POSIX'],
    packages=[
        'dbase32',
        'dbase32.tests',
    ],
    ext_modules=[
        Extension('dbase32._dbase32', **ext_kw),
    ],
    cmdclass={
        'test': Test,
        'benchmark': Benchmark,
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: C',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Database',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)

