Installing on Ubuntu
====================

D-Base32 packages are available for `Ubuntu`_ Raring in the
`Novacut Stable Releases PPA`_ and the `Novacut Daily Builds PPA`_.

Installation is easy. First add either the stable PPA::

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

Note if you add both the stable and the daily PPA, the versions in the daily
PPA will supersede the versions in the stable PPA.

Also see :doc:`bugs`.


.. _`Novacut Stable Releases PPA`: https://launchpad.net/~novacut/+archive/stable?field.series_filter=raring
.. _`Novacut Daily Builds PPA`: https://launchpad.net/~novacut/+archive/daily?field.series_filter=raring
.. _`Ubuntu`: http://www.ubuntu.com/

