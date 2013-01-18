RFC-3548 base32-encoding has an unfortunate property in that the sort order
of the encoded data is different than the binary data, for example:

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

This is because the characters in the RFC-3548 base32 encoding table aren't in
ASCII/UTF-8 sorted order, they are in this order::

    ABCDEFGHIJKLMNOPQRSTUVWXYZ234567
    
Whereas sorted order would be this::

    234567ABCDEFGHIJKLMNOPQRSTUVWXYZ

For space and performance reasons, a database might internally decode the
base32 doc IDs and build its indexes according to the compact, binary IDs.
This is an attractive option that we want to keep open.  But for simplicity
and compatibility, it can likewise be attractive to index according to the
base32 text, not to mention programmatic manipulation of the documents that
might sort or compare based on either the binary or base32 IDs.

These two approaching are going to face a giant problem as soon as one needs
to, say, request a range of document from the other, for example a query for
all docs such that::

    start_id <= doc._id <= end_id

The binary vs base32 indexes would disagree on what the starting and ending
document IDs in the database are, so this could easily translate into a
nonsense query like this::

    14 <= doc._id <= 3

To be clear, we consider this a total deal-breaker for Dmedia, and so we
aren't going to use RFC-3548 base32-encoding.  It would be a nasty design
wart that every implementation would have to battle.

So we're going to use some base32-encoding with a sorted alphabet, so the
question is, which one?


Simplest Solution
=================

Engineering-wise, it's attractive to chop off characters at the ends
so that the reverse-table is as small as possible (so it only needs to
contain the seven symbols ":;<=>?@").  This also probably has
advantages as far as adoption as this makes things simpler, and makes
table-free implementations possible.

When it comes to end-chopping, there are five options::

     0123456789ABCDEFGHIJKLMNOPQRSTUV WXYZ
    0 123456789ABCDEFGHIJKLMNOPQRSTUVW XYZ
    01 23456789ABCDEFGHIJKLMNOPQRSTUVWX YZ
    012 3456789ABCDEFGHIJKLMNOPQRSTUVWXY Z
    0123 456789ABCDEFGHIJKLMNOPQRSTUVWXYZ


The top option offers the max character diff from RFC-3548 (d=4), the 2nd
has (d=3), and the bottom three all thave (d=2).
