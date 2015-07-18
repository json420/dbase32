Installation
============

`Dbase32`_ packages are available for `Ubuntu`_ in the
`Novacut Stable Releases PPA`_ and the `Novacut Daily Builds PPA`_.


Install on Ubuntu
-----------------

Installation on Ubuntu is easy. First add either the stable PPA::

    sudo apt-add-repository ppa:novacut/stable
    sudo apt-get update

Or the daily PPA::

    sudo apt-add-repository ppa:novacut/daily
    sudo apt-get update

And then install the ``python3-dbase32`` package::

    sudo apt-get install python3-dbase32

Optionally install the ``python3-dbase32-doc`` package to have this
documentation available locally and offline::

    sudo apt-get install python3-dbase32-doc

After which the documentation can be browsed at:

    file:///usr/share/doc/python3-dbase32-doc/html/index.html

You can run the Dbase32 unit tests against the installed ``python3-dbase32`` package
like this::

    python3 -m dbase32.tests.run

Note that if you add both the stable and the daily PPA, the versions in the
daily PPA will supersede the versions in the stable PPA.



Source code
-----------

You can also download the source code tarball for each release `from
Launchpad`_.



bzr trunk
---------

Finally, can you grab the latest code from the `bzr trunk`_ branch like this::

    bzr checkout lp:dbase32

Or create your own branch for your own work like this::

    bzr branch lp:dbase32 lp:~/dbase32/mybranch
    bzr checkout lp:~/dbase32/mybranch

You can run the Dbase32 unit tests from within the source tree like this::

    ./setup.py test



Reporting bugs
--------------

The `dbase32 Launchpad project`_ is where all Dbase32 development is
coordinated, including bug tracking.

If you're using `Ubuntu`_ and have the ``python3-dbase32`` package installed,
the best way to file a bug is to open a terminal and run::

    ubuntu-bug python3-dbase32

This will automatically attach useful information to the bug report, which
can greatly help in diagnosing the problem.

Otherwise, please file a bug directly `through the web UI`_.



.. _`Dbase32`: https://launchpad.net/dbase32
.. _`Ubuntu`: http://www.ubuntu.com/
.. _`Novacut Stable Releases PPA`: https://launchpad.net/~novacut/+archive/ubuntu/stable
.. _`Novacut Daily Builds PPA`: https://launchpad.net/~novacut/+archive/ubuntu/daily
.. _`from Launchpad`: https://launchpad.net/dbase32/+download
.. _`bzr trunk`: https://code.launchpad.net/~dmedia/dbase32/trunk
.. _`dbase32 Launchpad project`: https://launchpad.net/dbase32
.. _`through the web UI`: https://bugs.launchpad.net/dbase32

