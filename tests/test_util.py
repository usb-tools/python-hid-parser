# SPDX-License-Identifier: MIT

import pytest

import hid_parser


@pytest.mark.parametrize(
    ('bits', 'size'),
    [
        (0, (0, 0)),
        (1, (0, 1)),
        (4, (0, 4)),
        (8, (1, 0)),
        (9, (1, 1)),
        (15, (1, 7)),
        (16, (2, 0)),
    ],
)
def test_bitnumber_value(bits, size):
    b = hid_parser.BitNumber(bits)

    assert int(b) == bits
    assert b.byte == size[0]
    assert b.bit == size[1]


@pytest.mark.parametrize(
    ('bits', 'desc'),
    [
        (0, '0bits'),
        (1, '1bit'),
        (4, '4bits'),
        (8, '1byte'),
        (9, '1byte 1bit'),
        (15, '1byte 7bits'),
        (16, '2bytes'),
    ],
)
def test_bitnumber_repr(bits, desc):
    assert repr(hid_parser.BitNumber(bits)) == desc
