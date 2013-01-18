Houston, We Have A Sorting Problem
==================================

No idea why this didn't dawn on me much earlier, but better late than never,
I guess.  There is a serious design problem with how we currently
base32-encode the file IDs, and this is something that we must fix before
we bless the final version one hashing protocol.

Standard RFC-3548 base32 encoding has an unfortunate property in that the sort
order of the encoded data is different than the binary data, for example:

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

This is because the symbols in the RFC-3548 base32 encoding table aren't in
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

To be clear, I consider this a total deal-breaker for Dmedia, and so we
are *not* going to use RFC-3548 base32 encoding in the final version 1
hashing protocol.  It would be a nasty design wart that every implementation
would have to battle.  And that does not an ecosystem make.

So we're going to use *some* base32 encoding with a sorted-order alphabet,
but the question is, which one?


Simplest Solution?
------------------

Perhaps the simplest solution is to use the same set of symbols as RFC-3548,
but with an encoding table in sorted order?  We might call it Sorted-Base32,
and it indeed gives us a base32 sort order that matches the binary sort
order, as you can see:

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

This provides the easiest migration path for Dmedia as we wouldn't have to
change the sub-directories used inside the FileStore layout (there are 1024
sub-directories, built using the first two characters of the base32-encoded
file IDs).

However, in terms of being good Internet citizens, this seems like a *really*
bad idea.  Especially if (knock on wood) our database-friendly encoding gets
widely used, we'd be doing everyone a disservice by popularizing an encoding
that on the surface looks exactly like RFC-3548, but is in fact 100% not the
same.

So let's rule out "Sorted-Base32".

With even a single character difference in the encoding alphabet, it only
takes a mere dozen or so random IDs to have an *extremely* high probably of
getting an ID containing the symbol not present in the other alphabet.  At
which point the coder knows the RFC-3548 looking-encoding is in fact not,
and they can fix their code.

The problem of picking the character set comes down to this: here are 36
symbols, and we need to pick 4 to exclude::

    0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ

RFC-3548 excludes ``0``, ``1``, ``8``, and  ``9``, so for our set to be
different, we need to include at least one of those.  The general goal is to
remove symbols that look too much alike so that the alphabet has a good
signal-to-noise ratio for us human folk.

However, before we dive into that, I'd like to step back and look at some
engineering properties that might help us narrow the search.


Engineering Considerations
--------------------------

Engineering-wise, it's attractive to chop off characters at the ends so that
the reverse-table doesn't require any unnecessary "dead-spots" (as, for
example, the RFC-3548 set requires for ``8`` and ``9``).

When it comes to end-chopping, there are five permutations::

     0123456789ABCDEFGHIJKLMNOPQRSTUV WXYZ
    0 123456789ABCDEFGHIJKLMNOPQRSTUVW XYZ
    01 23456789ABCDEFGHIJKLMNOPQRSTUVWX YZ
    012 3456789ABCDEFGHIJKLMNOPQRSTUVWXY Z
    0123 456789ABCDEFGHIJKLMNOPQRSTUVWXYZ

The topmost offers the max possible symbol difference from RFC-3548 (d=4), the
2nd has (d=3), and the bottom three all have (d=2).  So any of them would
work, as we only need d=1.

It may seem like splitting hairs, but I'm a big believer 
