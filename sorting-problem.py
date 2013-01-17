#!/usr/bin/python3

from dbase32 import db32enc
from base64 import b32encode
from collections import namedtuple

Tup = namedtuple('Tup', 'i data hex b32 db32')

items = []
for i in range(16):
    num = 16 * i + i
    data = num.to_bytes(1, 'little') * 5
    hexdata = '{:02x}'.format(num) * 5
    b32 = b32encode(data).decode('utf-8')
    db32 = db32enc(data)
    t = Tup(i, data, hexdata, b32, db32)
    items.append(t)

sort1 = sorted(items, key=lambda t: t.data)
sort2 = sorted(items, key=lambda t: t.b32)
sort3 = sorted(items, key=lambda t: t.db32)

print('    =============  ===========  ===========')
print('       Binary         Base32       D-Base32')
print('    =============  ===========  ===========')
for (a, b, c) in zip(sort1, sort2, sort3):
    print('    {:>2} {}  {:>2} {}  {:2} {}'.format(a.i, a.hex, b.i, b.b32, c.i, c.db32))
print('    =============  ===========  ===========')

