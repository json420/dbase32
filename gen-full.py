from dbase32.misc import *

forward = gen_forward('012Z')
reverse = gen_reverse(forward)
start = get_start(forward)
end = get_end(forward)

for line in iter_c('DB32', forward, reverse, start, end):
    print(line)
