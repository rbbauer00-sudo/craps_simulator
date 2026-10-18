ALL_NUMS = frozenset((2,3,4,5,6,7,8,9,10,11,12))

BOX_NUMS = frozenset((4,5,6,8,9,10))
FIELD_NUMS = frozenset((2,3,4,9,10,11,12))

CRAPS_NUMS = frozenset((2,3,12))
HORN_NUMS = frozenset((2,3,11,12))

ATS_SMALL_NUMS = frozenset({2, 3, 4, 5, 6})
ATS_TALL_NUMS = frozenset({8, 9, 10, 11, 12})
ATS_ALL_NUMS = ATS_SMALL_NUMS | ATS_TALL_NUMS

HOP_TARGETS = {
    tuple(sorted((d1, d2)))
    for d1 in range(6, 0, -1)
    for d2 in range(d1, 0, -1)
    if d1 + d2 not in (2, 3, 11, 12)
}

BASE32 = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
