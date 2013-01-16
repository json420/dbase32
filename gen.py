
possible = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
assert ''.join(sorted(set(possible))) == possible


def build_forward(remove):
    remove = set(remove)
    assert len(remove) == 4
    assert remove.issubset(possible)
    forward = set(possible) - remove
    assert len(forward) == 32
    return ''.join(sorted(forward))


def build_reverse_iter(forward):
    start = ord(forward[0])
    stop = ord(forward[-1]) + 1
    for d in range(start, stop):
        c = chr(d)
        r = forward.find(c)
        assert r < 32
        if r < 0:
            r = 255
        yield(r, d, c)


def build_reverse(forward):
    assert ''.join(sorted(set(forward))) == forward
    assert set(forward).issubset(possible)
    return tuple(build_reverse_iter(forward))


def iter_c(forward, reverse):
    yield '#define START {!r}'.format(ord(forward[0]))
    yield '#define END {!r}'.format(ord(forward[-1]))
    yield ''
    yield 'static const uint8_t forward[{}] = "{}";'.format(
        len(forward), forward
    )
    yield ''
    yield 'static const uint8_t reverse[{}] = {{'.format(len(reverse))
    for (r, d, c) in reverse:
        yield '    {:>3},  // {} {!r}'.format(r, d, c)
    yield '};'


def iter_python(forward, reverse):
    yield 'forward = {!r}'.format(forward)
    yield ''
    yield 'reverse = ('
    for (r, d, c) in reverse:
        yield '    {:>3},  # {} {!r}'.format(r, d, c)
    yield ')'
    


forward = build_forward('012Z')
reverse = build_reverse(forward)

print('')
for line in iter_c(forward, reverse):
    print(line)

print('')
for line in iter_python(forward, reverse):
    print(line)


