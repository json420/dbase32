Changelog
=========


1.5 (unreleased)
----------------

`Download Dbase32 1.5`_

Changes:

    *   `lp:1473688`_ --- Update unit tests for Python 3.5 compatibility ---
        Python 3.5 makes some changes in the exact ``TypeError`` messages used
        when it comes to the Python Buffer Protocol.  The unit tests now use the
        newer ``TypeError`` format for Python >= 3.5, otherwise use the older
        format.  A small update was also made in the pure-Python reference
        implementation as it emulates the ``TypeError`` behavior of the C
        implementation (and both are subject to the same unit tests).

    *   ``dbase32/benchmark.py`` now imports the functions in question from
        their containing module, eliminating the overhead of module attribute
        access.  As such, the benchmark is now more representative.  Also, the
        pure-Python Dbase32 functions have been dropped from the benchmark, as
        have the timing attack tests.

    *   ``DBASE32_INSTRUMENT_BUILD=true ./setup.py build_ext`` will now
        instrument the C extension with asan, ubsan.

    *   Build C extensions with the following extra compile args:

        *   -pedantic-errors
        *   -Wsign-compare
        *   -Wsign-conversion

        Some small changes were also made in the C extension as needed for
        ``-Wsign-conversion``.

    *   A number of small fixes where made in the comments, doc-strings, and
        documentation.

    *   Drop "official" support for Python 3.3 as Dbase32 hasn't been actively
        tested under 3.3 for some time.



1.4 (December 2014)
-------------------

`Download Dbase32 1.4`_

Changes:

    *   Add ``"# doctest: -IGNORE_EXCEPTION_DETAIL"`` to all Sphinx
        documentation examples that raise exceptions, plus fix several such
        examples that still used the exception messages from Dbase32 v1.1.

    *   :attr:`dbase32.DB32ALPHABET`, :attr:`dbase32.MAX_BIN_LEN`, and
        :attr:`dbase32.MAX_TXT_LEN` are now imported from the specific backend
        implementation being used (rather than being separately defined in
        ``dbase32/__init__.py``).

    *   Add new :attr:`dbase32.using_c_extension` attribute that 3rd party
        software can use in their unit tests and/or runtime initialization to
        verify that the Dbase32 C extension is being used.

    *   The `dbase32._dbase32.c`_ internal API functions now use the same
        ``(buf, len)`` argument ordering as standard C library functions like
        ``memmem()``, etc::

            static uint8_t
            dbase32_encode(const uint8_t *bin_buf, const size_t bin_len,
                                 uint8_t *txt_buf, const size_t txt_len)

            static uint8_t
            dbase32_decode(const uint8_t *txt_buf, const size_t txt_len,
                                 uint8_t *bin_buf, const size_t bin_len)

            static uint8_t
            dbase32_validate(const uint8_t *txt_buf, const size_t txt_len)

        (Previously ``(len, buf)`` argument ordering was used.)

    *   The above internal C API functions are no longer declared as ``inline``
        because it provides almost no measurable performance improvement, plus
        inlining will carry a larger code-size penalty when more public Dbase32
        API is added in the future (ie., when there are more consumers of these
        internal API functions).

    *   Build the C extension with ``'-std=gnu11'`` as this will soon be the GCC
        default.

    *   Sundry fixes and improvements in documentation and comments.



1.3 (September 2014)
--------------------

`Download Dbase32 1.3`_

.. note::

    Even if you doubt whether the data you're encoding/decoding/validating is
    security sensitive, please err on the side of caution and upgrade to Dbase32
    1.3 anyway!

Security fixes:

    *   `lp:1359862`_ --- Prevent information leakage in cache hit/miss for
        non-error conditions --- in the C implementation, the reverse table is
        now rotated 42 bytes to the left so that all valid entries fit in a
        single 64-byte cache line, and likewise so that all valid entries are at
        least balanced between two 32-byte cache lines (16 entries are in each
        32-byte cache line); note that although the C implementation of Dbase32
        is now constant-time when validating or decoding a *valid* ID (on
        systems with a 64-byte or larger cache-line size), cache hits and misses
        can still leak information about what bytes are in an *invalid* ID; this
        is seemingly not exploitable when applications directly Dbase32-encode
        secret data, but this certainly could be exploited when attacker
        controlled input interacts with secret data such that when the secret is
        known, a valid Dbase32 ID should be produced.

        For example, this is an exploitable pattern that should be avoided::

            # Don't do this!  Cache hit/miss will leak information about secret!
            if isdb32(standard_xor(secret, attacker_controlled_input)):
                print('Authorized')
            else:
                print('Rejected')

        Although the above example is rather contrived, it still demonstrates
        how decoding and validating with Dbase32, if done carelessly, can leak
        exploitable timing information that could allow an attacker to
        incrementally guess a secret, thereby dramatically reducing the
        effective search space of said secret.

        For more details, please see :doc:`security`.

Other changes:

    *   Move ``_dbase32`` (the C implementation) to ``dbase32._dbase32``; using
        a package-relative import (rather than an absolute import) makes life
        easier for developers and packagers as the ``dbase32`` package can no
        longer inadvertently import ``_dbase32`` from another location in the
        Python path; prior to this change, importing ``dbase32`` from within the
        source tree would fall-back to importing ``_dbase32`` from the
        system-wide ``python3-dbase32`` package if it was installed; now
        ``dbase32`` will only use the C extension from the same package
        location, will never fall-back to a version installed elsewhere

    *   Rename ``dbase32.fallback`` (the Python implementation) to
        ``dbase32._dbase32py``, just to be consistent with the above naming



1.2 (August 2014)
-----------------

`Download Dbase32 1.2`_

Security fixes:

    *   `lp:1359828`_ --- Mitigate timing attacks when decoding with
        :func:`dbase32.db32dec()` or validating with
        :func:`dbase32.check_db32()` --- the C implementation now always decodes
        or validates the entire ID rather than stopping at the first base-32
        "block" (8 bytes) containing an error; note that as cache hits and
        misses in the ``DB32_REVERSE`` table can still leak information, the C
        implementations of these functions still can't be considered
        constant-time; however, Dbase32 1.2 is certainly a step in the right
        direction, and as such, all Dbase32 users are strongly encouraged to
        upgrade, especially those who might be encoding/decoding/validating
        security sensitive data

    *   When an ID contains invalid characters, :func:`dbase32.db32dec()` and
        :func:`dbase32.check_db32()` now raise a ``ValueError`` containing a
        ``repr()`` of the entire ID rather than only the first invalid character
        encountered; although this in some ways makes the unit tests a bit less
        rigorous (because you can't test agreement on the specific offending
        character), this is simply required in order to mitigate the timing
        attack issues; on the other hand, for downstream developers it's
        probably more helpful to see the entire problematic value anyway; note
        that this is an *indirect* API breakage for downstream code that might
        have had unit tests that check these ValueError messages; still, also
        note that backward compatibility in terms of the direct API usage hasn't
        been broken and wont be at any time in the 1.x series



1.1 (April 2014)
----------------

`Download Dbase32 1.1`_

Changes:

    * Be more pedantic in C extension, don't assume sizeof(uint8_t) is 1 byte

    * ``setup.py test`` now does static analysis with `Pyflakes`_, fix a few
      small issues discovered by the same



1.0 (March 2014)
----------------

`Download Dbase32 1.0`_

Initial 1.x stable API release, for which no breaking API changes are expected
throughout the lifetime of the 1.x series.

Changes:

    * Rename former ``dbase32.log_id()`` function to :func:`dbase32.time_id()`;
      note that for backward compatibility there is still a ``dbase32.log_id``
      alias, but this may be dropped at some point in the future

    * Tweak :func:`dbase32.time_id()` C implementation to no longer use
      ``temp_ts`` variable

    * Fix some formerly broken `Sphinx`_ doctests, plus ``setup.py`` now runs
      said Sphinx doctests

    * Add documentation about security properties of validation functions, best
      practices thereof



.. _`Download Dbase32 1.5`: https://launchpad.net/dbase32/+milestone/1.5
.. _`Download Dbase32 1.4`: https://launchpad.net/dbase32/+milestone/1.4
.. _`Download Dbase32 1.3`: https://launchpad.net/dbase32/+milestone/1.3
.. _`Download Dbase32 1.2`: https://launchpad.net/dbase32/+milestone/1.2
.. _`Download Dbase32 1.1`: https://launchpad.net/dbase32/+milestone/1.1
.. _`Download Dbase32 1.0`: https://launchpad.net/dbase32/+milestone/1.0

.. _`lp:1359862`: https://bugs.launchpad.net/dbase32/+bug/1359862
.. _`lp:1359828`: https://bugs.launchpad.net/dbase32/+bug/1359828
.. _`lp:1473688`: https://bugs.launchpad.net/dbase32/+bug/1473688
.. _`Pyflakes`: https://launchpad.net/pyflakes
.. _`Sphinx`: http://sphinx-doc.org/
.. _`dbase32._dbase32.c`: http://bazaar.launchpad.net/~dmedia/dbase32/trunk/view/head:/dbase32/_dbase32.c

