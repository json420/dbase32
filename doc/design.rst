Design Rationale
================

This is the rationale for why `Dbase32`_ is designed the way it is.


Sort order problem
------------------

Standard `RFC-3548 Base32`_ encoding has an unfortunate property in that the
sort order of the encoded data is different than the binary data, for example::

    =============  ===========
       Binary         Base32
    =============  ===========
     0 0000000000  13 3XO53XO5
     1 1111111111  14 53XO53XO
     2 2222222222  15 77777777
     3 3333333333   0 AAAAAAAA
     4 4444444444   1 CEIRCEIR
     5 5555555555   2 EIRCEIRC
     6 6666666666   3 GMZTGMZT
     7 7777777777   4 IRCEIRCE
     8 8888888888   5 KVKVKVKV
     9 9999999999   6 MZTGMZTG
    10 aaaaaaaaaa   7 O53XO53X
    11 bbbbbbbbbb   8 RCEIRCEI
    12 cccccccccc   9 TGMZTGMZ
    13 dddddddddd  10 VKVKVKVK
    14 eeeeeeeeee  11 XO53XO53
    15 ffffffffff  12 ZTGMZTGM
    =============  ===========

This is because the symbols in the RFC-3548 base32 alphabet aren't in
ASCII/UTF-8 sorted order, they are in this order::

    ABCDEFGHIJKLMNOPQRSTUVWXYZ234567

Whereas sorted order would be this::

    234567ABCDEFGHIJKLMNOPQRSTUVWXYZ

For space and performance reasons, a database might internally decode the
base32 doc IDs and build its indexes according to the compact, binary IDs.
This is an attractive option that we want to keep open.  But for simplicity
and compatibility, it can likewise be attractive to index according to the
base32 text.  Not to mention all the programmatic manipulation that will
happen with the docs on the application side of things, where sorting and
comparison of the doc IDs is not uncommon.

But these two approaches are going to face a giant problem as soon as one
needs to, say, request a range of documents from the other, for example a
query for all docs such that::

    start_id <= doc._id <= end_id

The binary vs base32 indexes would disagree on what the first and final
document IDs in the database are, so on the other end, this could easily
translate into a nonsense query like::

    14 <= doc_N <= 3

To be clear, I consider this a total deal-breaker for `Dmedia`_, and so we
are *not* going to use RFC-3548 Base32 encoding in the final version 1
hashing protocol.  It would be a nasty design wart that every implementation
would have to battle.  And that does not an ecosystem make.

So we're going to use *some* base32 encoding with a sorted-order alphabet,
but the question is, which one?


Simplest solution?
------------------

Perhaps the simplest solution is to use the same set of symbols as RFC-3548,
but with the alphabet in sorted order?  We might call it Sorted-Base32, and it
indeed gives us a base32 sort order that matches the binary sort order, as you
can see::

    =============  ===========  ===========
       Binary         Base32       S-Base32
    =============  ===========  ===========
     0 0000000000  13 3XO53XO5   0 22222222
     1 1111111111  14 53XO53XO   1 46CL46CL
     2 2222222222  15 77777777   2 6CL46CL4
     3 3333333333   0 AAAAAAAA   3 AGTNAGTN
     4 4444444444   1 CEIRCEIR   4 CL46CL46
     5 5555555555   2 EIRCEIRC   5 EPEPEPEP
     6 6666666666   3 GMZTGMZT   6 GTNAGTNA
     7 7777777777   4 IRCEIRCE   7 IXVRIXVR
     8 8888888888   5 KVKVKVKV   8 L46CL46C
     9 9999999999   6 MZTGMZTG   9 NAGTNAGT
    10 aaaaaaaaaa   7 O53XO53X  10 PEPEPEPE
    11 bbbbbbbbbb   8 RCEIRCEI  11 RIXVRIXV
    12 cccccccccc   9 TGMZTGMZ  12 TNAGTNAG
    13 dddddddddd  10 VKVKVKVK  13 VRIXVRIX
    14 eeeeeeeeee  11 XO53XO53  14 XVRIXVRI
    15 ffffffffff  12 ZTGMZTGM  15 ZZZZZZZZ
    =============  ===========  ===========

This provides the easiest migration path for `Dmedia`_ as we wouldn't have to
change the sub-directories used inside the `FileStore`_ layout (there are 1024
sub-directories, built using the first two characters of the base32-encoded
file IDs).

However, in terms of being good Internet citizens, this seems like a *really*
bad idea.  Especially if (knock on wood) our database-friendly encoding gets
widely used, we'd be doing everyone a disservice by popularizing an encoding
that on the surface looks exactly like RFC-3548, but is in fact 100% not the
same.

So let's rule out Sorted-Base32.

With even a single character difference in the encoding alphabet, it only
takes a mere dozen or so random IDs to have an *extremely* high probably of
getting an ID containing the symbol not present in the other alphabet.  At
which point the programmer knows the encoding that looked very much like
RFC-3548 is in fact not, and they can fix their code.

The problem of picking the character set comes down to this: here are 36
symbols, and we need to remove 4 or them::

    0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ

RFC-3548 excludes ``0``, ``1``, ``8``, and  ``9``, so for our set to be
different, we need to include at least one of those.  The general goal is to
remove symbols that look too much alike so that the alphabet has a good
signal-to-noise ratio for us human folk.

However, before we dive into that, I'd like to step back and look at some
engineering properties that might help us narrow the search.


Engineering considerations
--------------------------

In terms of engineering aesthetic, it's attractive to chop off characters at
the ends so that the reverse-table doesn't require any unnecessary internal
"dead-spots" (as, for example, the RFC-3548 set requires for ``8`` and ``9``).

When it comes to end-chopping, there are five permutations::

     0123456789ABCDEFGHIJKLMNOPQRSTUV WXYZ
    0 123456789ABCDEFGHIJKLMNOPQRSTUVW XYZ
    01 23456789ABCDEFGHIJKLMNOPQRSTUVWX YZ
    012 3456789ABCDEFGHIJKLMNOPQRSTUVWXY Z
    0123 456789ABCDEFGHIJKLMNOPQRSTUVWXYZ

The topmost is already used by `RFC-4648 base32hex`_, which I rule out below.

After that, the 2nd from the top differs from RFC-3548 by three symbols, and
the bottom three all differ by two symbols.  So any of the bottom four would
work, as we only need our alphabet to differ by a single symbol.

It may seem like splitting hairs, but I think even small improvements in how
quickly one can understand a technology can have a big impact on its adoption
success.  We certainly don't want something that seems *more* complex than
RFC-3548.

We have some solid engineering problems we're solving, issues that might
effect anyone using base32-encoded IDs, especially in document oriented
databases, distributed file systems, etc.  Even so, a non-standard base32
encoding means we're going out on limb here.  It would be far better for
`Dmedia`_ and `Novacut`_ if the encoding we come up with was also adopted
by others.

In addition to the above engineering advantages (for specific problems),
I'd also like to have something that's just a tiny bit simpler and more
elegant than RFC-3548. Not the same, and certainly not worse.  Better, even
if only by a smidge.

So instead of opening Pandora's box in an epic search for the best 32 letters,
which would mean a reverse-table that is full of more dead spots than RFC-3548,
I think we should restrict ourselves to picking the best of the five above
options.


Signal to noise
---------------

I'm unconvinced that one set of 32 can be much better than another because it
depends so heavily on the font being used, and the people of the world of
course aren't all using the same font.  Opinions are all over the map, for the
most part.

The one place where there seems to be near-consensus is around::

    0O (zero and oh)
    1I (one and eye)

It is for this reason that I decided *not* to use `RFC-4648 base32hex`_, a
base32 encoding with this sorted-order alphabet::

    0123456789ABCDEFGHIJKLMNOPQRSTUV

Although base32hex does have the desired property of preserving the sort-order,
there aren't many implementations readily available (for example, the Python
standard library lacks a base32hex implementation).  And as long as we need
to provide our own implementation, we might as well use an encoding that is
as good as possible for our use case.

There are also some advantages to using a unique encoding.  Our goal is not to
encode arbitrary data, but only to encode well-formed IDs with very specific
constraints.  A unique encoding can help convey the context and the intended
use.  Think of it like branding.  Plus, we hope these IDs show up all over the
place, especially on the web, so it would be very handy if web crawlers could
usually distinguish our IDs from run-of-the-mill base32 data.

Anyway, there is near-consensus on ``0O`` and ``1I`` being a problem, but less
agreement on how to fix it.  Remove the number, remove the letter, or even
remove both?

Fortunately, our hands are tied and we can only remove the numbers, so lets do
that.  Now we're down to three options, with two more symbols to remove::

     23456789ABCDEFGHIJKLMNOPQRSTUVWX YZ
    2 3456789ABCDEFGHIJKLMNOPQRSTUVWXY Z
    23 456789ABCDEFGHIJKLMNOPQRSTUVWXYZ

We can remove ``YZ``, ``2Z``, or ``23``.  My vote is to remove ``2Z``, as they
look quite similar to each other, and I feel that probably provides the best
overall signal-to-noise.  So that gives us this alphabet::

    3456789ABCDEFGHIJKLMNOPQRSTUVWXY

As far as I know, this set of symbols (regardless of order) isn't used in any
existing base32 encoding.


Dmedia base32
-------------

I'm calling our encoding Dbase32 (D is for `Dmedia`_, and D is for Database).
It has the desired property of preserving the sort order, as you can see::

    =============  ===========  ===========  ===========
       Binary         Base32       S-Base32      Dbase32
    =============  ===========  ===========  ===========
     0 0000000000  13 3XO53XO5   0 22222222   0 33333333
     1 1111111111  14 53XO53XO   1 46CL46CL   1 57BK57BK
     2 2222222222  15 77777777   2 6CL46CL4   2 7BK57BK5
     3 3333333333   0 AAAAAAAA   3 AGTNAGTN   3 9FSM9FSM
     4 4444444444   1 CEIRCEIR   4 CL46CL46   4 BK57BK57
     5 5555555555   2 EIRCEIRC   5 EPEPEPEP   5 DODODODO
     6 6666666666   3 GMZTGMZT   6 GTNAGTNA   6 FSM9FSM9
     7 7777777777   4 IRCEIRCE   7 IXVRIXVR   7 HWUQHWUQ
     8 8888888888   5 KVKVKVKV   8 L46CL46C   8 K57BK57B
     9 9999999999   6 MZTGMZTG   9 NAGTNAGT   9 M9FSM9FS
    10 aaaaaaaaaa   7 O53XO53X  10 PEPEPEPE  10 ODODODOD
    11 bbbbbbbbbb   8 RCEIRCEI  11 RIXVRIXV  11 QHWUQHWU
    12 cccccccccc   9 TGMZTGMZ  12 TNAGTNAG  12 SM9FSM9F
    13 dddddddddd  10 VKVKVKVK  13 VRIXVRIX  13 UQHWUQHW
    14 eeeeeeeeee  11 XO53XO53  14 XVRIXVRI  14 WUQHWUQH
    15 ffffffffff  12 ZTGMZTGM  15 ZZZZZZZZ  15 YYYYYYYY
    =============  ===========  ===========  ===========

Because Dbase32 is *not* designed to encode arbitrary data, but instead is
designed only to encode our well-formed IDs, we're *not* supporting padding.
Data to be encoded must be a multiple of 5 bytes in length, and text to be
decoded must be a multiple of 8 characters in length.

This strict validation is good in terms of enforcing correctness in higher-level
code, and it makes the implementation easier, eliminates a lot of potential
spots for security goofs.


Note on lowercase
-----------------

Anyone with typographic savvy will tell you that using lowercase letters will
make the IDs more readable, and I don't disagree.  This is something that folks
put a lot of thought into for the `z-base-32`_ encoding.

However, I personally think the overall readability of our *schema* is far more
important than the readability of our encoded IDs.  After all, there is nothing
to *read* in the IDs as they are random, meaningless values, not words.
Whereas the *words* used in rest of the schema have been careful chosen to be
both clear and concise, and are *always* lowercase.

The reason I prefer uppercase IDs in the schema is it helps differentiate the
meaningless garble from the bits you actually will *read*.  For me, it helps
push the IDs into the background, and brings out rest of the schema more clearly
in the foreground.

For example, consider this `Novacut`_ edit node with lowercase IDs::

    {
        "_id": "jg444obnf5juunspcce5ypik",
        "type": "novacut/node",
        "time": 1234567892,
        "audio": [],
        "node": {
            "type": "video/sequence",
            "src": [
                "3hhsrsvxt5zgy2b6ljpn457p",
                "rxjm24dmcrz4ys6l6fopdqrx"
            ]
        }
    }

And the same with uppercase IDs::

    {
        "_id": "JG444OBNF5JUUNSPCCE5YPIK",
        "type": "novacut/node",
        "time": 1234567892,
        "audio": [],
        "node": {
            "type": "video/sequence",
            "src": [
                "3HHSRSVXT5ZGY2B6LJPN457P",
                "RXJM24DMCRZ4YS6L6FOPDQRX"
            ]
        }
    }

Or consider this `Dmedia`_ file document with lowercase IDs::

    {
        "_id": "224zy4wmnxnkjpin6u5hmwimjigjm2hma5ioci3qgdiw2ldt",
        "type": "dmedia/file",
        "time": 1355254766.513135,
        "atime": 1355388946,
        "bytes": 25272864,
        "origin": "user",
        "stored": {
            "btvd5cs2hm4obdlmac2l7wzm": {
                "copies": 0,
                "mtime": 1353160147
            },
            "dla4ndzrw2lxepf3rv7yhmon": {
                "copies": 1,
                "mtime": 1353160147
            },
            "papbeh4zvqv5upo3l3h4rtur": {
                "copies": 1,
                "mtime": 1353392010,
                "verified": 1360256513
            }
        }
    }

And the same with uppercase IDs::

    {
        "_id": "224ZY4WMNXNKJPIN6U5HMWIMJIGJM2HMA5IOCI3QGDIW2LDT",
        "type": "dmedia/file",
        "time": 1355254766.513135,
        "atime": 1355388946,
        "bytes": 25272864,
        "origin": "user",
        "stored": {
            "BTVD5CS2HM4OBDLMAC2L7WZM": {
                "copies": 0,
                "mtime": 1353160147
            },
            "DLA4NDZRW2LXEPF3RV7YHMON": {
                "copies": 1,
                "mtime": 1353160147
            },
            "PAPBEH4ZVQV5UPO3L3H4RTUR": {
                "copies": 1,
                "mtime": 1353392010,
                "verified": 1360256513
            }
        }
    }


.. _`Dbase32`: https://launchpad.net/dbase32
.. _`RFC-3548 Base32`: https://tools.ietf.org/html/rfc4648
.. _`Novacut`: https://launchpad.net/novacut
.. _`Dmedia`: https://launchpad.net/dmedia
.. _`FileStore`: https://launchpad.net/filestore
.. _`RFC-4648 base32hex`: https://tools.ietf.org/html/rfc4648#section-7
.. _`z-base-32`: http://philzimmermann.com/docs/human-oriented-base-32-encoding.txt

