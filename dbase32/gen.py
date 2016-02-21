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
Helper functions for generating and validating base-32 encoding tables.
"""

from collections import namedtuple
import optparse


POSSIBLE = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
TYPE_ERROR = '{}: need a {!r}; got a {!r}: {!r}'
Reverse = namedtuple('Reverse', 'i key value')

# Standard RFC-3548 Base32:
B32_FORWARD = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'

# Defaults when running as a script:
REMOVE = '012Z'
NAME = 'db32'


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
        raise ValueError(
            'len(remove) != 4: [{}] {!r}'.format(len(remove), remove)
        )
    remove_set = set(remove)
    if len(remove_set) != 4:
        raise ValueError(
            'len(set(remove)) != 4: [{}] {!r}'.format(
                len(remove_set), remove
            )
        )
    if not remove_set.issubset(POSSIBLE):
        raise ValueError(
            'remove: {!r} not a subset of {!r}'.format(remove, POSSIBLE)
        )
    forward = set(POSSIBLE) - remove_set
    assert len(forward) == 32
    return ''.join(sorted(forward))


def check_forward(forward):
    if not isinstance(forward, str):
        raise TypeError(
            TYPE_ERROR.format('forward', str, type(forward), forward)
        )
    if len(forward) != 32:
        raise ValueError(
            'len(forward) != 32: [{}] {!r}'.format(len(forward), forward)
        )
    forward_set = set(forward)
    if len(forward_set) != 32:
        raise ValueError(
            'len(set(forward)) != 32: [{}] {!r}'.format(
                len(forward_set), forward
            )
        )
    if not forward_set.issubset(POSSIBLE):
        raise ValueError(
            'forward: {!r} not a subset of {!r}'.format(forward, POSSIBLE)
        )
    return forward


def get_start(forward):
    check_forward(forward)
    return ord(min(forward))


def get_end(forward):
    check_forward(forward)
    return ord(max(forward))


def _gen_reverse_iter(forward):
    start = get_start(forward)
    end = get_end(forward)
    for i in range(256):
        if start <= i <= end:
            key = chr(i)
            value = forward.find(key)
            assert value < 32
            if value < 0:
                value = 255
            yield Reverse(i, key, value)
        else:
            yield Reverse(i, None, 255)


def gen_reverse(forward):
    check_forward(forward)
    return tuple(_gen_reverse_iter(forward))


def rotate_left(reverse, offset):
    assert isinstance(offset, int) and 0 <= offset < 64
    rotated = list(reverse[offset:])
    rotated.extend(reverse[:offset])
    return tuple(rotated)


def count_valid(reverse):
    count = 0
    for r in reverse:
        if r.value != 255:
            assert 0 <= r.value <= 31
            count += 1
    return count


def count_cache_32(reverse):
    return (count_valid(reverse[0:32]), count_valid(reverse[32:64]))


def group_empty_iter(reverse, size=19):
    buf = []
    for r in reverse:
        if r.key is None:
            buf.append(r)
            if len(buf) >= size:
                yield buf
                buf = []
        else:
            if buf:
                yield buf
                buf = []
            yield r
    if buf:
        yield buf


def iter_c(name, forward, reverse, start, end):
    yield 'static const uint8_t {}_START = {};'.format(name, start)
    yield 'static const uint8_t {}_END = {};'.format(name, end)

    yield 'static const uint8_t {}_FORWARD[{}] = "{}";'.format(
        name, len(forward), forward
    )

    yield 'static const uint8_t {}_REVERSE[{}] = {{'.format(
        name, len(reverse)
    )

    for item in group_empty_iter(reverse):
        if isinstance(item, list):
            yield '    {},'.format(','.join(str(r.value) for r in item))
        else:
            r = item
            yield '    {:>3},  // {!r} [{:>2}] -> [{:>2}]'.format(
                r.value, r.key, r.i, r.i - 42
            )

    yield '};'


def iter_python(name, forward, reverse, start, end):
    yield '{}_START = {}'.format(name, start)
    yield '{}_END = {}'.format(name, end)
    yield '{}_FORWARD = {!r}'.format(name,  forward)

    yield '{}_REVERSE = ('.format(name)
    for item in group_empty_iter(reverse):
        if isinstance(item, list):
            yield '    {},'.format(','.join(str(r.value) for r in item))
        else:
            r = item
            yield '    {:>3},  # {!r} [{:>2}]'.format(r.value, r.key, r.i)

    yield ')'


def get_c32_rep(rotated):
    accum = []
    for r in rotated[0:32]:
        if r.value == 255:
            accum.append(' ')
        else:
            accum.append(r.key)
    accum.append('  ')
    for r in rotated[32:64]:
        if r.value == 255:
            accum.append(' ')
        else:
            accum.append(r.key)
    first = ''.join(accum)
    second = ('_' * 32) + '  ' + ('_' * 32)
    return (first, second)


if __name__ == '__main__':

    parser = optparse.OptionParser()
    parser.add_option('--rfc',
        help='generate standard RFC-3548 base32 tables',
        action='store_true',
        default=False,
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

    if options.rfc:
        forward = B32_FORWARD
        name = 'b32'
    else:
        forward = gen_forward(options.remove)
        name = options.name
    reverse = gen_reverse(forward)
    start = get_start(forward)
    end = get_end(forward)
    line_iter = (iter_python if options.python else iter_c)

    if not options.python:
        reverse = rotate_left(reverse, 42)

    print('')
    for line in line_iter(name.upper(), forward, reverse, start, end):
        print(line)
    print('')

