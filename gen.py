from collections import namedtuple

Encoding = namedtuple('Encoding', 'name removed title desc start end forward reverse')

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
    start = ord(min(forward))
    stop = ord(max(forward)) + 1
    for (i, d) in enumerate(range(start, stop)):
        c = chr(d)
        r = forward.find(c)
        assert r < 32
        if r < 0:
            r = 255
        yield (r, d, c, i)


def build_reverse(forward):
    assert len(set(forward)) == len(forward)
    assert set(forward).issubset(possible)
    return tuple(build_reverse_iter(forward))


def iter_c(t):
    name = t.name.upper()
    yield '// {}: {}: {}'.format(name, t.title, t.desc)
    yield '// [removes {}]'.format(', '.join(l for l in t.removed))
    yield 'static const uint8_t {}_START = {!r};'.format(t.name.upper(), t.start)
    yield 'static const uint8_t {}_END = {!r};'.format(t.name.upper(), t.end)
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
    yield '# {}: {}: {}'.format(name, t.title, t.desc)
    yield '# [removes {}]'.format(', '.join(l for l in t.removed))
    yield '{}_START = {!r}'.format(name, t.start)
    yield '{}_END = {!r}'.format(name, t.end)
    yield '{}_FORWARD = {!r}'.format(name, t.forward)
    yield '{}_REVERSE = ('.format(name)
    for (r, d, c, i) in t.reverse:
        yield '    {:>3},  # {} {!r} [{:>2}]'.format(r, d, c, i)
    yield ')'


def build_encoding(name, remove, title, desc, forward=None):
    if forward is None:
        forward = build_forward(remove)
    assert set(possible) - set(remove) == set(forward)
    assert len(set(remove)) == 4
    assert set(remove).issubset(possible)
    start = ord(min(forward))
    end = ord(max(forward))
    reverse = build_reverse(forward)
    return Encoding(name, remove, title, desc, start, end, forward, reverse)


def print_python(*encodings):
    for enc in encodings:
        for line in iter_python(enc):
            print(line)
        print('')

 
def print_c(*encodings):
    for enc in encodings:
        for line in iter_c(enc):
            print(line)
        print('')


b32 = build_encoding('b32', '0189',
    'RFC-3548', 'different binary vs encoded sort order (deal breaker!)',
    forward='ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
)

sb32 = build_encoding('sb32', '0189',
    'Sorted-Base32', 'standard RFC-3548 letters, but in sorted order'
)

db32 = build_encoding('db32', '012Z',
    'Dmedia-Base32', 'non-standard 3-9, A-Y letters'
)

izob32 = build_encoding('izob32', 'EMOC',
    'Base32-by-IZO', 'The great bearded one speaketh'
)

hb32 = build_encoding('hb32', 'DMAN',
    'Hippie-Base32', 'max unique-snowflake units away from RFC-3548'
)

zb32 = build_encoding('zb32', '0lv2'.upper(),
    'z-base-32',
    'http://philzimmermann.com/docs/human-oriented-base-32-encoding.txt'
)


encodings = (b32, sb32, db32, zb32)
for enc in encodings:
    print_c(enc)
for enc in encodings:
    print_python(enc)

