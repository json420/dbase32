Changelog
=========


1.2 (August 2014)
-----------------

`Download Dbase32 1.2`_

Changes:

    * `Mitigate timing attacks`_ when decoding with :func:`dbase32.db32dec()` or
      validating with :func:`dbase32.check_db32()`; note that as cache hits and
      misses (especially L1) in the DB32_REVERSE table can still leak
      information, the C implementations of these functions still can't be
      considered constant-time; however, Dbase32 1.2 is certainly a step in the
      right direction, and as such; all Dbase32 users are strongly encouraged to
      upgrade, especially those who might be encoding/decoding/validating
      security sensitive data

    * When an ID contains invalid characters, :func:`dbase32.db32dec()` and
      :func:`dbase32.check_db32()` now raise a ``ValueError`` containing a
      ``repr()`` of the entire ID rather than only the first invalid character
      encountered; although this in some ways makes the unit tests a bit less
      rigorous (because you can't test agreement on the specific offending
      character), this is simply required in order to mitigate the timing attack
      issues; on the other hand, for downstream developers it's probably more
      helpful to see the entire problematic value anyway; note that this is an
      *indirect* API breakage for downstream code that might have had unit tests
      that check these ValueError messages; still, also note that backward
      compatibility in terms of the direct API usage hasn't been broken and wont
      be at any time in the 1.x series

*Even if you doubt whether the data you're encoding/decoding/validating is
security sensitive, please err on the side of caution and upgrade to Dbase32 1.2
anyway!*



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



.. _`Download Dbase32 1.2`: https://launchpad.net/dbase32/+milestone/1.2
.. _`Download Dbase32 1.1`: https://launchpad.net/dbase32/+milestone/1.1
.. _`Download Dbase32 1.0`: https://launchpad.net/dbase32/+milestone/1.0

.. _`Mitigate timing attacks`: https://bugs.launchpad.net/dbase32/+bug/1359828
.. _`Pyflakes`: https://launchpad.net/pyflakes
.. _`Sphinx`: http://sphinx-doc.org/

