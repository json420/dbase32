from dbase32 import alphabet

assert ''.join(sorted(set(alphabet))) == alphabet
assert len(alphabet) == 32

start = ord(alphabet[0])
stop = ord(alphabet[-1]) + 1

print('alphabet = {!r}'.format(alphabet))

print('r_alphabet = (')
for i in range(start, stop):
    c = chr(i)
    index = alphabet.find(c)
    assert index < 32
    if index < 0:
        index = 255
    print('    {:>3},  # {} {!r}'.format(index, i, c))
print(')')
