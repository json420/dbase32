Security Considerations
=======================



C vs. Python implementation
---------------------------

For both performance and security reasons, only the `C implementation`_ of
:mod:`dbase32` is recommended for production use.

The `Python implementation`_ is intended merely as a reference against which the
correctness of the C implementation can be more rigorously evaluated.

.. warning::

    As the `Python implementation`_ does *not* attempt to mitigate timing
    attacks, it is fundamentally *less* secure than the `C implementation`_!

    The Python implementation is focused on simplicity and correctness; but as a
    consequence, it leaks a considerable amount of exploitable timing
    information.

It's specifically helpful for the Python implementation to take a much different
approach than the C implementation, but one that still produces identical
behavior under the scrutiny of the unit tests to which both implementations are
subject.

Some notable differences in the Python implementation:

    *   It doesn't use a *rotated* ``DB32_REVERSE`` table as Python provides no
        way to guarantee that all valid entries in the resulting table would fit
        within a single 64-byte cache-line anyway

    *   :func:`dbase32.db32dec()` does an error check at each byte, and stops
        upon the first invalid byte encountered

    *   :func:`dbase32.isdb32()` and :func:`dbase32.check_db32()` are
        implemented using ``frozenset.issuperset()``, do not directly use the
        ``DB32_REVERSE`` table

The Python implementation is *never* constant-time when encoding IDs, and
likewise is *never* constant-time when decoding or validating IDs, not even when
the ID is a well-formed, valid Dbase32 ID.

For security reasons, 3rd party applications may want to ensure that the Dbase32
C implementation is being used, which they can do like this:

>>> import dbase32
>>> dbase32.using_c_extension is True  # doctest: +SKIP
True

If the `C implementation`_ isn't working on a particular architecture, please
`file a bug against Dbase32`_.



Timing attacks
--------------

The `C implementation`_ of :mod:`dbase32` employs several of techniques to
mitigate timing attacks.

However, even the C implementation can leak exploitable timing information in
some scenarios.

So it's important to understand the scenarios under which the C implementation
is guaranteed to be constant-time, and likewise the scenarios under which it can
still leak exploitable timing information.

Some of these scenarios depend upon whether the target architecture has a
32-byte cache-line size (eg., ARM Cortex-A9 and earlier) or a 64-byte cache-line
size (eg., ARM Cortex-A15 and later, plus all modern Intel and AMD systems).

Scenarios under which the `C implementation`_ of :mod:`dbase32` is
constant-time:

    *   On architectures with a 32-byte (or larger) cache-line size,
        :func:`dbase32.db32enc()`, :func:`dbase32.random_id()`, and
        :func:`dbase32.time_id()` are all constant-time with respect to the
        content of the data being encoding; this is because the entire
        ``DB32_FORWARD`` table fits within a single 32-byte cache-line, and
        because no error checking is needed aside from the initial length check

    *   When decoding or validating *valid* Dbase32 IDs on architectures with a
        64-byte (or larger) cache-line size, :func:`dbase32.db32dec()`,
        :func:`dbase32.isdb32()`, and :func:`dbase32.check_db32()` are all
        constant-time with respect to the content of the text being decoded or
        validated; this is because in the *rotated* ``DB32_REVERSE`` table, all
        *valid* entries fit within a single 64-byte cache-line, and because
        these functions always optimistically decode or validate the entire ID,
        only do a single error check at the end (rather than doing an error
        check per byte or per base32-block)

On the other hand, the `C implementation`_ of :mod:`dbase32` **can leak
exploitable timing information** in these scenarios:

    *   On architectures with a 32-byte (or smaller) cache-line size, even when
        decoding or validating *valid* Dbase32 IDs, :func:`dbase32.db32dec()`,
        :func:`dbase32.isdb32()`, and :func:`dbase32.check_db32()` all leak
        timing information that can provide insight into the exact content of
        the text being decoded or validated; this is because even in the
        *rotated* ``DB32_REVERSE`` table, the *valid* entries in the table still
        span two 32-byte cache lines

    *   When decoding or validating *invalid* Dbase32 IDs on architectures with
        a 64-byte cache-line size, :func:`dbase32.db32dec()`,
        :func:`dbase32.isdb32()`, and :func:`dbase32.check_db32()` all leak
        timing information that can provide insight into the exact content of
        the text being decoding or validated; this is because the full
        ``DB32_REVERSE`` table spans four 64-byte cache lines

In summary, when it comes to the `C implementation`_ of :mod:`dbase32` on
contemporary architectures:

    1.  Encoding is always constant-time

    2.  Decoding and validating is *only* constant-time when the architecture
        has a 64-byte cache-line size *and* when the text in question is a
        well-formed, valid Dbase32 ID

    3.  Otherwise the act of decoding or validating leaks timing information
        that can provide insight into the exact content of the the text in
        question; this is true when the architecture has a 32-byte cache-line
        size, and is likewise true when the text in question is not a
        well-formed, valid Dbase32 ID


Using Dbase32 IDs in filenames, URLs
------------------------------------

Dbase32 has a nice security property in that a well-formed Dbase32 ID *should*
be safe to use directly in filenames and URLs, without any special escaping or
extra validation.

.. warning::

    Please don't assume that *valid* Dbase32 IDs are safe to use without
    escaping in all situations!  This Dbase32 security property has only been
    well considered in the context of filenames and URLs, so don't carelessly
    assume it applies elsewhere!

This is a central concern for the `Dmedia FileStore`_, where file IDs from
untrusted input are used to construct the full filenames by which data is read
from the file-system.  Without properly validating this untrusted input, the
``FileStore`` could easily be vulnerable to directory traversal attacks.

:mod:`dbase32` is rather unique among base32 implementations in that its
high-performance validation functions allow you to check whether some encoded
text is well-formed without actually decoding it.

You should *never* trust the :mod:`dbase32` validation functions as your sole
security mechanism, but you're encouraged to use these validation functions
liberally.  In particular, it's a good idea to use both :func:`dbase32.isdb32()`
and :func:`dbase32.check_db32()` in different, independent security layers.  For
example:

>>> from dbase32 import isdb32, check_db32
>>> isdb32('../very/naughty/')
False
>>> check_db32('../very/naughty/')  # doctest: -IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
  ...
ValueError: invalid Dbase32: '../very/naughty/'

The `C implementation`_ of these validation functions are *extremely*
performant, so don't let performance concerns stop you from using them!


.. _`C implementation`: http://bazaar.launchpad.net/~dmedia/dbase32/trunk/view/head:/dbase32/_dbase32.c
.. _`Python implementation`: http://bazaar.launchpad.net/~dmedia/dbase32/trunk/view/head:/dbase32/_dbase32py.py
.. _`file a bug against Dbase32`: https://bugs.launchpad.net/dbase32
.. _`Dmedia FileStore`: https://launchpad.net/filestore

