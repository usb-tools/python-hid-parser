# SPDX-License-Identifier: MIT

import sys

import pytest

import hid_parser


def test_baseitem():
    item = hid_parser.BaseItem(1, 2)

    assert item.offset == hid_parser.BitNumber(1)
    assert item.size == hid_parser.BitNumber(2)


@pytest.mark.skipif(sys.version_info < (3, 8), reason='repr behaves differently before 3.8')
def test_baseitem_repr():
    assert repr(hid_parser.BaseItem(1, 2)) == 'BaseItem(offset=1bit, size=2bits)'


def test_mainitem():
    assert issubclass(hid_parser.MainItem, hid_parser.BaseItem)

    item = hid_parser.MainItem(0, 0, 0b000, -1, 1)

    assert item.logical_min == -1
    assert item.logical_max == 1
    assert item.physical_min is None
    assert item.physical_max is None

    assert item.constant is False
    assert item.data is True
    assert item.relative is False
    assert item.absolute is True

    item = hid_parser.MainItem(0, 0, 0b001, -1, 1, -1, 1)

    assert item.logical_min == -1
    assert item.logical_max == 1
    assert item.physical_min == -1
    assert item.physical_max == 1

    assert item.constant is True
    assert item.data is False
    assert item.relative is False
    assert item.absolute is True

    item = hid_parser.MainItem(0, 0, 0b100, -1, 1, -1, 1)

    assert item.logical_min == -1
    assert item.logical_max == 1
    assert item.physical_min == -1
    assert item.physical_max == 1

    assert item.constant is False
    assert item.data is True
    assert item.relative is True
    assert item.absolute is False


def test_variableitem():
    assert issubclass(hid_parser.VariableItem, hid_parser.MainItem)

    item = hid_parser.VariableItem(0, 0, 0b00000000, hid_parser.Usage(0x0001, 0x0030), -1, 1)

    assert item.usage == hid_parser.Usage(0x0001, 0x0030)

    assert item.wrap is False
    assert item.linear is False
    assert item.preferred_state is False
    assert item.null_state is False
    assert item.buffered_bytes is False
    assert item.bitfield is True

    item = hid_parser.VariableItem(0, 0, 0b00001000, hid_parser.Usage(0x0001, 0x0030), -1, 1)

    assert item.wrap is True
    assert item.linear is False
    assert item.preferred_state is False
    assert item.null_state is False
    assert item.buffered_bytes is False
    assert item.bitfield is True

    item = hid_parser.VariableItem(0, 0, 0b00010000, hid_parser.Usage(0x0001, 0x0030), -1, 1)

    assert item.wrap is False
    assert item.linear is True
    assert item.preferred_state is False
    assert item.null_state is False
    assert item.buffered_bytes is False
    assert item.bitfield is True

    item = hid_parser.VariableItem(0, 0, 0b00100000, hid_parser.Usage(0x0001, 0x0030), -1, 1)

    assert item.wrap is False
    assert item.linear is False
    assert item.preferred_state is True
    assert item.null_state is False
    assert item.buffered_bytes is False
    assert item.bitfield is True

    item = hid_parser.VariableItem(0, 0, 0b01000000, hid_parser.Usage(0x0001, 0x0030), -1, 1)

    assert item.wrap is False
    assert item.linear is False
    assert item.preferred_state is False
    assert item.null_state is True
    assert item.buffered_bytes is False
    assert item.bitfield is True

    item = hid_parser.VariableItem(0, 0, 0b10000000, hid_parser.Usage(0x0001, 0x0030), -1, 1)

    assert item.wrap is False
    assert item.linear is False
    assert item.preferred_state is False
    assert item.null_state is False
    assert item.buffered_bytes is True
    assert item.bitfield is False


@pytest.mark.skipif(sys.version_info < (3, 8), reason='repr behaves differently before 3.8')
def test_variableitem_repr():
    assert repr(hid_parser.VariableItem(1, 2, 0, hid_parser.Usage(0x0001, 0x0030), -1, 1)) == \
        'VariableItem(offset=1bit, size=2bits, usage=Usage(page=Generic Desktop Controls, usage=X))'


def test_variableitem_compliance():
    with pytest.warns(hid_parser.HIDComplianceWarning):
        hid_parser.VariableItem(1, 2, 0, hid_parser.Usage(0x0001, 0x0001), -1, 1)

    with pytest.warns(None):
        hid_parser.VariableItem(1, 2, 0, hid_parser.Usage(0x0001, 0x0030), -1, 1)

    with pytest.warns(None):
        hid_parser.VariableItem(1, 2, 0, hid_parser.Usage(0x0001, 0x0000), -1, 1)

    with pytest.warns(None):
        hid_parser.VariableItem(1, 2, 0, hid_parser.Usage(0x0000, 0x0000), -1, 1)


def test_arrayitem():
    assert issubclass(hid_parser.ArrayItem, hid_parser.MainItem)

    usages = [
        hid_parser.Usage(0x0001, 0x0030),
        hid_parser.Usage(0x0001, 0x0031),
    ]

    item = hid_parser.ArrayItem(0, 0, 0, usages, -1, 1)

    assert item.usages == usages


@pytest.mark.skipif(sys.version_info < (3, 8), reason='repr behaves differently before 3.8')
def test_arrayitem_repr():
    usages = [
        hid_parser.Usage(0x0001, 0x0030),
        hid_parser.Usage(0x0001, 0x0031),
    ]
    print(repr(hid_parser.ArrayItem(1, 2, 0, usages, -1, 1)))
    assert repr(hid_parser.ArrayItem(1, 2, 0, usages, -1, 1)) == (
        'ArrayItem(\n'
        '    offset=1bit, size=2bits,\n'
        '    usages=[\n'
        '        Usage(page=Generic Desktop Controls, usage=X),\n'
        '        Usage(page=Generic Desktop Controls, usage=Y),\n'
        '    ],\n'
        ')'
    )


def test_arrayitem_compliance():
    usages = [
        hid_parser.Usage(0x0001, 0x0030),
        hid_parser.Usage(0x0001, 0x0031),
    ]

    with pytest.warns(hid_parser.HIDComplianceWarning):
        hid_parser.ArrayItem(1, 2, 0, usages, -1, 1)

    with pytest.warns(None):
        hid_parser.ArrayItem(1, 2, 0, usages, -1, 1)

    with pytest.warns(None):
        hid_parser.ArrayItem(1, 2, 0, usages, -1, 1)

    with pytest.warns(None):
        hid_parser.ArrayItem(1, 2, 0, usages, -1, 1)
