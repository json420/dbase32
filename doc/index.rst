D-Base32
========

The `D-Base32`_ encoding is base-32 variant designed for document oriented
databases and applications, specifically for encoding document IDs.

D-Base32 uses an alphabet whose letters are in ASCII/UTF-8 sorted order.  This
means that unlike `RFC-3548 Base32`_ encoding, the sort-order of the encoded
data will match the sort-order of the binary data.

The :mod:`dbase32` package provides a Python3 implementation of the encoding,
with both a high-performance C extension and a pure-Python fallback.  The C
versions are automatically selected when available.

Example usage:

>>> from dbase32 import db32enc, db32dec
>>> db32enc(b'Bytes')
'BCVQBSEM'
>>> db32dec('BCVQBSEM')
b'Bytes'

`D-Base32`_ is being developed as part of the `Novacut`_ project.  D-Base32
packages are available for Ubuntu in the `Novacut Stable Releases PPA`_ and the
`Novacut Daily Builds PPA`_.

If you have questions or need help getting started with D-Base32, please stop
by the `#novacut`_ IRC channel on freenode.

D-Base32 is licensed `LGPLv3+`_.

Contents:

.. toctree::
    :maxdepth: 2

    dbase32
    design


.. _`D-Base32`: https://launchpad.net/dbase32
.. _`RFC-3548 Base32`: http://tools.ietf.org/html/rfc4648
.. _`LGPLv3+`: http://www.gnu.org/licenses/lgpl-3.0.html
.. _`Novacut`: https://wiki.ubuntu.com/Novacut
.. _`Novacut Stable Releases PPA`: https://launchpad.net/~novacut/+archive/stable
.. _`Novacut Daily Builds PPA`: https://launchpad.net/~novacut/+archive/daily
.. _`#novacut`: http://webchat.freenode.net/?channels=novacut
