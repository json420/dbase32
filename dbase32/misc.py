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
Helper functions for defining and validating an base32 encoding.
"""

POSSIBLE = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

TYPE_ERROR = '{}: need a {!r}; got a {!r}: {!r}'


def gen_forward(remove):
    """
    Generate a forward-table by specifying the symbols to *remove*.
    
    For example:

    >>> gen_forward('0123')
    '456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    Or:

    >>> gen_forward('ABYZ')
    '0123456789CDEFGHIJKLMNOPQRSTUVWX'

    """
    if not isinstance(remove, str):
        raise TypeError(
            TYPE_ERROR.format('remove', str, type(remove), remove)
        )
    if len(remove) != 4:
        raise ValueError('len(remove) != 4; got {!r}'.format(remove))
    remove_set = set(remove)
    if len(remove_set) != 4:
        raise ValueError(
            'remove must contain 4 unique symbols; got {!r}'.format(remove)
        )
    if not remove_set.issubset(POSSIBLE):
        raise ValueError(
            'remove: {!r} not a subset of {!r}'.format(remove, POSSIBLE)
        )
    forward = set(POSSIBLE) - remove_set
    assert len(forward) == 32
    return ''.join(sorted(forward))

