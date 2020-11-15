# SPDX-License-Identifier: MIT

import pytest

import hid_parser


@pytest.mark.parametrize(
    ('flags', 'expected'),
    [
        (0b000000000, 'Data, Array, Absolute'),
        (0b000000001, 'Constant, Array, Absolute'),
        (0b000000010, 'Data, Variable, Absolute, No Wrap, Linear, Preferred State, No Null position, Bit Field'),
        (0b000000100, 'Data, Array, Relative'),
        (0b000001000, 'Data, Array, Absolute'),
        (0b000010000, 'Data, Array, Absolute'),
        (0b000100000, 'Data, Array, Absolute'),
        (0b001000000, 'Data, Array, Absolute'),
        (0b010000000, 'Data, Array, Absolute'),
        (0b100000000, 'Data, Array, Absolute'),
        (0b000000010, 'Data, Variable, Absolute, No Wrap, Linear, Preferred State, No Null position, Bit Field'),
        (0b000000011, 'Constant, Variable, Absolute, No Wrap, Linear, Preferred State, No Null position, Bit Field'),
        (0b000000110, 'Data, Variable, Relative, No Wrap, Linear, Preferred State, No Null position, Bit Field'),
        (0b000001010, 'Data, Variable, Absolute, Wrap, Linear, Preferred State, No Null position, Bit Field'),
        (0b000010010, 'Data, Variable, Absolute, No Wrap, Non Linear, Preferred State, No Null position, Bit Field'),
        (0b000100010, 'Data, Variable, Absolute, No Wrap, Linear, No Preferred State, No Null position, Bit Field'),
        (0b001000010, 'Data, Variable, Absolute, No Wrap, Linear, Preferred State, Null State, Bit Field'),
        (0b010000010, 'Data, Variable, Absolute, No Wrap, Linear, Preferred State, No Null position, Bit Field'),
        (0b100000010, 'Data, Variable, Absolute, No Wrap, Linear, Preferred State, No Null position, Buffered Bytes'),
        (0b111111111, 'Constant, Variable, Relative, Wrap, Non Linear, No Preferred State, Null State, Buffered Bytes'),
    ],
)
def test_main_item_desc(flags, expected):
    assert hid_parser.ReportDescriptor._get_main_item_desc(flags) == expected
