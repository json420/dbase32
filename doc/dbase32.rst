:mod:`dbase32` Reference
========================

.. py:module:: dbase32
    :synopsis: base32-encoding with a sorted-order alphabet (for databases)

The `D-Base32`_ encoding is a base-32 variant designed for document-oriented
databases, specifically for encoding document IDs.

D-Base32 uses an alphabet whose symbols are in ASCII/UTF-8 sorted order. This
means that unlike standard `RFC-3548 Base32`_ encoding, the sort-order of the
encoded data will match the sort-order of the binary data.  For details, please
see the see the :doc:`design`.



Tutorial
--------

Encode a ``bytes`` instance with :func:`db32enc()`:

>>> from dbase32 import db32enc
>>> db32enc(b'binary foo')
'FCNPVRELI7J9FUUI'

Decode the resulting ``str`` instance with :func:`db32dec()`:

>>> from dbase32 import db32dec
>>> db32dec('FCNPVRELI7J9FUUI')
b'binary foo'

Use :func:`isdb32()` to test whether you have a valid D-Base32 encoded ID.  It
will return ``True`` if the ID is valid:

>>> from dbase32 import isdb32
>>> isdb32('FCNPVRELI7J9FUUI')
True

And will return ``False`` if the ID contains invalid letters or is the wrong
length:

>>> isdb32('AAAAAAAA')
True
>>> isdb32('AAAAAAAZ')
False
>>> isdb32('AAAAAAA')
False

You can likewise use :func:`check_db32()` to validate an ID.  It will return
``None`` if the ID is valid:

>>> from dbase32 import check_db32
>>> check_db32('FCNPVRELI7J9FUUI')

And will raise a ``ValueError`` if the ID contains invalid letters or is the
wrong length:

>>> check_db32('AAAAAAAA')
>>> check_db32('AAAAAAAZ')
Traceback (most recent call last):
  ...
ValueError: invalid D-Base32 letter: Z
>>> check_db32('AAAAAAA')
Traceback (most recent call last):
  ...
ValueError: len(text) is 7, need 8 <= len(text) <= 96

When you don't actually want the decoded ID, it's much faster to validate with
:func:`isdb32()` or :func:`check_db32()` than to validate with :func:`db32dec()`
and throw away the needlessly decoded value.

Lastly, use :func:`random_id()` to generate a D-Base32 encoded ID with entropy
from ``/dev/urandom``.  By default it will return a 120-bit (15-byte) ID, which
will be 24 characters in length when D-Base32 encoded:

>>> from dbase32 import random_id
>>> random_id()
'UGT6U75VTJL8IRBBPRFONKOQ'

The *numbytes* keyword argument defaults to ``15``, but you can override this
to get an ID with a different length.  Typically you would only use this for
unit testing, for example to create a well-formed 240-bit (30-byte) Dmedia file
ID, which will be 48 characters in length when D-Base32 encoded:

>>> random_id(30)
'AU8HC68B9IC6AY6B3NHWOGCI9VK4MTOUSFLWRD7TLQBC56MN'

This:

>>> _id = random_id(15)

Is the equivalent of this:

>>> _id = db32enc(os.urandom(15))

Although note that the C implementation of :func:`random_id()` is faster than
the above because it does everything internally with no back-and-forth between
Python and C.

If for any reason you want to start with the binary ID, simply use
``os.urandom()`` directly, and then encode it with :func:`db32enc()` when
needed.


Well-formed IDs
---------------

D-Base32 is not designed to encode arbitrary data.  Instead, it's designed only
to encode well-formed IDs like those used in `Dmedia`_ and `Novacut`_.

Unlike standard `RFC-3548 Base32`_ encoding, D-Base32 does *not* support
padding.  The binary data must always be a multiple of 40 bits (5 bytes) in
length.

Well-formed *data* to be encoded must be a ``bytes`` instance that meets the
following condition::

    5 <= len(data) <= 60 and len(data) % 5 == 0

If this condition isn't met, :func:`db32enc()` will raise a ``ValueError``.

In addition to only containing characters in :data:`DB32ALPHABET`, well-formed
*text* to be decoded must be an ``str`` instance that meets the following
condition::

    8 <= len(text) <= 96 and len(text) % 8 == 0

If this condition isn't met, both :func:`db32dec()` and :func:`check_db32()`
will raise a ``ValueError``.  Likewise, if this condition isn't met,
:func:`isdb32()` will return ``False``.



Functions
---------

.. function:: db32enc(data)

    Encode *data* as D-Base32 text.

    An ``str`` instance is returned:

    >>> db32enc(b'Bytes')
    'BCVQBSEM'

    *data* must be a ``bytes`` instance that meets the following condition::

        5 <= len(data) <= 60 and len(data) % 5 == 0


.. function:: db32dec(text)

    Decode D-Base32 *text*.

    A ``bytes`` instance is returned:

    >>> db32dec('BCVQBSEM')
    b'Bytes'

    *text* must be an ``str`` instance meets the following condition::

        8 <= len(text) <= 96 and len(text) % 8 == 0

    A ``ValueError`` is raised if the above condition is not met, or if *text*
    contains any letters not in the D-Base32 alphabet.


.. function:: isdb32(text)

    Return ``True`` if *text* contains a valid D-Base32 encoded ID.

    >>> isdb32('39AYA9AY')
    True
    >>> isdb32('27AZ27AZ')
    False

    This function will only return ``True`` if *text* contains only valid
    D-Base32 letters, and if *text* meets following condition::

        8 <= len(text) <= 96 and len(text) % 8 == 0


.. function:: check_db32(text)

    Raise a ``ValueError`` if *text* is not a valid D-Base32 encoded ID.

    This function will raise a ``ValueError`` if *text* contains any letters
    that aren't part of the D-Base32 alphabet.  For example:

    >>> check_db32('39AYA9AY')
    >>> check_db32('39AY27AZ')
    Traceback (most recent call last):
      ...
    ValueError: invalid D-Base32 letter: 2

    This function will likewise raise a ``ValueError`` if *text* doesn't meet
    the following condition::

        8 <= len(text) <= 96 and len(text) % 8 == 0


.. function:: random_id(numbytes=15)

    Return a random ID built from *numbytes* worth of entropy.

    The ID is returned as an ``str`` containing the D-Base32 encoded version:

    >>> random_id()
    'XM4OINLIPO6VVF549TWYNK89'
    >>> random_id(5)
    'V37E4B38'

    The random data is from ``os.urandom()``.



Constants
---------

A few handy constants:


.. data:: DB32ALPHABET

    >>> DB32ALPHABET = '3456789ABCDEFGHIJKLMNOPQRSTUVWXY'


.. data:: MAX_BIN_LEN

    Max length of binary data that :func:`db32enc()` accepts for encoding.

    >>> MAX_BIN_LEN = 60  # 480 bits


.. data:: MAX_TXT_LEN

    Max length of text data that :func:`db32dec` accepts for decoding.

    >>> MAX_TXT_LEN = 96


.. data:: RANDOM_BITS

    Default size (in bits) of the *decoded* ID generated by :func:`random_id()`

    >>> RANDOM_BITS = 120


.. data:: RANDOM_BYTES

    Default size (in bytes) of the *decoded* ID generated by :func:`random_id()`

    >>> RANDOM_BYTES = 15


.. data:: RANDOM_B32LEN

    Default size (in characters) of the ID generated by :func:`random_id()`

    >>> RANDOM_B32LEN = 24


.. _`D-Base32`: https://launchpad.net/dbase32
.. _`RFC-3548 Base32`: http://tools.ietf.org/html/rfc4648
.. _`Novacut`: https://launchpad.net/novacut
.. _`Dmedia`: https://launchpad.net/dmedia
