from collections import namedtuple

Encoding = namedtuple('Encoding', 'name removed forward reverse desc')

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
    for (i, d) in enumerate(range(start, stop)):
        c = chr(d)
        r = forward.find(c)
        assert r < 32
        if r < 0:
            r = 255
        yield (r, d, c, i)


def build_reverse(forward):
    assert ''.join(sorted(set(forward))) == forward
    assert set(forward).issubset(possible)
    return tuple(build_reverse_iter(forward))


def iter_c(t):
    name = t.name.upper()
    yield '// {}: {}'.format(name, t.desc)
    yield 'static const uint8_t {}_START = {!r};'.format(t.name.upper(), ord(t.forward[0]))
    yield 'static const uint8_t {}_END = {!r};'.format(t.name.upper(), ord(t.forward[-1]))
    yield 'static const uint8_t {}_FORWARD[{}] = "{}";'.format(
        name, len(t.forward), t.forward
    )
    yield 'static const uint8_t {}_REVERSE[{}] = {{'.format(
        name, len(t.reverse)
    )
    for (r, d, c, i) in t.reverse:
        yield '    {:>3},  // {} {!r} [{:>2}]'.format(r, d, c, i)
    yield '};'


def iter_python(t):
    name = t.name.upper()
    yield '# {}: {}'.format(name, t.desc)
    yield '{}_START = {!r}'.format(name, ord(t.forward[0]))
    yield '{}_END = {!r}'.format(name, ord(t.forward[-1]))
    yield '{}_FORWARD = {!r}'.format(name, t.forward)
    yield '{}_REVERSE = ('.format(name)
    for (r, d, c, i) in t.reverse:
        yield '    {:>3},  # {} {!r} [{:>2}]'.format(r, d, c, i)
    yield ')'


def build_encoding(name, remove, desc):
    forward = build_forward(remove)
    reverse = build_reverse(forward) 
    return Encoding(name, remove, forward, reverse, desc)


def print_python(*encodings):
    for enc in encodings:
        for line in iter_python(enc):
            print(line)
        print('')

 
def print_c(*encodings):
    for enc in encodings:
        print('')
        for line in iter_c(enc):
            print(line)
        print('')


db32 = build_encoding('db32', '012Z',
    'non-standard 3-9, A-Y letters (sorted order)'
)

sb32 = build_encoding('sb32', '0189',
    'standard RFC-3548 letters, but in sorted order'
)


print_c(db32, sb32)
print_python(db32, sb32)

