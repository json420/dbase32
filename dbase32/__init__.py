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
`dbase32` - base32-encoding with a sorted-order alphabet (for databases).

For example:

>>> from dbase32 import db32enc, db32dec
>>> db32enc(b'binary foo')
'FCNPVRELI7J9FUUI'
>>> db32dec('FCNPVRELI7J9FUUI')
b'binary foo'

"""

try:
    from ._dbase32 import (
        DB32ALPHABET,
        MAX_BIN_LEN,
        MAX_TXT_LEN,
        db32enc,
        db32dec,
        isdb32,
        check_db32,
        random_id,
        time_id,
        db32_relpath,
        db32_abspath,
    )
    using_c_extension = True
except ImportError:
    from ._dbase32py import (
        DB32ALPHABET,
        MAX_BIN_LEN,
        MAX_TXT_LEN,
        db32enc,
        db32dec,
        isdb32,
        check_db32,
        random_id,
        time_id,
        db32_relpath,
        db32_abspath,
    )
    using_c_extension = False


__version__ = '1.6.1'
__all__ = (
    'DB32ALPHABET',
    'MAX_BIN_LEN',
    'MAX_TXT_LEN',
    'db32enc',
    'db32dec',
    'isdb32',
    'check_db32',
    'random_id',
    'time_id',
    'db32_relpath',
    'db32_abspath',
)

RANDOM_BITS = 120
RANDOM_BYTES = 15
RANDOM_B32LEN = 24

# For backward-compatability with Dbase32 <= 0.10; at some point in the
# future we may want to drop this:
log_id = time_id

