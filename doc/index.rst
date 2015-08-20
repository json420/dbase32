Dbase32
=======

The `Dbase32`_ encoding is a base32 variant designed for document-oriented
databases, specifically for encoding document IDs.

Dbase32 uses an alphabet whose symbols are in ASCII/UTF-8 sorted order::

    3456789ABCDEFGHIJKLMNOPQRSTUVWXY

This means that unlike `RFC-3548 Base32`_ encoding, the sort-order of the
encoded data will match the sort-order of the binary data.

:mod:`dbase32` provides a Python3 implementation of the encoding, with both a
high-performance C extension and a pure-Python fallback.

Example encoding and decoding:

>>> from dbase32 import db32enc, db32dec
>>> db32enc(b'binary foo')
'FCNPVRELI7J9FUUI'
>>> db32dec('FCNPVRELI7J9FUUI')
b'binary foo'

:mod:`dbase32` also provides high-performance validation functions that allow
you to sanitize untrusted input without decoding the IDs.  For example:

>>> from dbase32 import isdb32, check_db32
>>> isdb32('../very/naughty/')
False
>>> check_db32('../very/naughty/')  # doctest: -IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
  ...
ValueError: invalid Dbase32: '../very/naughty/'

Dbase32 is being developed as part of the `Novacut`_ project. Packages are
available for `Ubuntu`_ in the `Novacut Stable Releases PPA`_ and the
`Novacut Daily Builds PPA`_.

If you have questions or need help getting started with Dbase32, please stop
by the `#novacut`_ IRC channel on freenode.

Dbase32 is licensed `LGPLv3+`_, requires `Python 3.4`_ or newer, and fully
supports `Python 3.5`_.

Contents:

.. toctree::
    :maxdepth: 2

    install
    dbase32
    security
    design
    changelog


.. _`Dbase32`: https://launchpad.net/dbase32
.. _`RFC-3548 Base32`: https://tools.ietf.org/html/rfc4648
.. _`LGPLv3+`: https://www.gnu.org/licenses/lgpl-3.0.html
.. _`Novacut`: https://wiki.ubuntu.com/Novacut
.. _`Novacut Stable Releases PPA`: https://launchpad.net/~novacut/+archive/ubuntu/stable
.. _`Novacut Daily Builds PPA`: https://launchpad.net/~novacut/+archive/ubuntu/daily
.. _`#novacut`: https://webchat.freenode.net/?channels=novacut
.. _`Ubuntu`: http://www.ubuntu.com/
.. _`Python 3.4`: https://docs.python.org/3.4/
.. _`Python 3.5`: https://docs.python.org/3.5/

