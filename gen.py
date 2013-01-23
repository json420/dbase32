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

import optparse

import dbase32
from dbase32 import misc


REMOVE = '012Z'
NAME = 'db32'


parser = optparse.OptionParser(
    usage='%prog',
	version=dbase32.__version__,
)
parser.add_option('-r',
    dest='remove',
    help='symbols to remove; default is {!r}'.format(REMOVE),
    default=REMOVE,
)
parser.add_option('-n',
    dest='name',
    help='encoding name; default is {!r}'.format(NAME),
    default=NAME,
)
parser.add_option('-p',
    dest='python',
    help='generate Python tables (instead of C)',
    action='store_true',
    default=False,
)
(options, args) = parser.parse_args()


forward = misc.gen_forward(options.remove)
reverse = misc.gen_reverse(forward)
start = misc.get_start(forward)
end = misc.get_end(forward)
name = options.name.upper()
line_iter = (misc.iter_python if options.python else misc.iter_c)


print('')
for line in line_iter(name, forward, reverse, start, end):
    print(line)
print('')
