def build_reverse_iter(forward):
    start = ord(min(forward))
    end = ord(max(forward))
    for i in range(256):
        if start <= i <= end:
            c = chr(i)
            r = forward.find(c)
            assert r < 32
            if r < 0:
                r = 255
        else:
            c = None
            r = 255
        yield (r, c, i)

def do_iter(reverse):
    buf = []
    for (r, c, i) in reverse:
        if c is None:
            buf.append(str(r))
            if len(buf) >= 16:
                yield buf
                buf = []
        else:
            if buf:
                yield buf
                buf = []
            yield (r, c, i)
    if buf:
        yield buf


def iter_c(name, forward):  
    start = ord(min(forward))
    end = ord(max(forward))

    reverse = tuple(build_reverse_iter(forward))

    yield 'static const uint8_t {}_FORWARD[{}] = "{}";'.format(
        name, len(forward), forward
    )
    yield 'static const uint8_t {}_REVERSE[{}] = {{'.format(
        name, len(reverse)
    )

    for item in do_iter(reverse):
        if isinstance(item, list):
            yield '    {},'.format(','.join(item))
        else:
            (r, c, i) = item
            yield '    {:>3},  // {!r} [{:>2}]'.format(r, c, i)

    yield '};'



forward = '3456789ABCDEFGHIJKLMNOPQRSTUVWXY'


for line in iter_c('DB32', forward):
    print(line)




#reverse = tuple(build_reverse_iter(forward))
#count = 0
#for item in do_iter(reverse):
#    print(item)
#    if isinstance(item, list):
#        count += len(item)
#    else:
#        count += 1

#print(count)
