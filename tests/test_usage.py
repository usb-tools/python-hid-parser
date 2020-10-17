# SPDX-License-Identifier: MIT

import pytest

import hid_parser


def test_create():
    usage = hid_parser.Usage(0x1234, 0x4321)

    assert usage.page == 0x1234
    assert usage.usage == 0x4321

    usage = hid_parser.Usage(extended_usage=0x12344321)

    assert usage.page == 0x1234
    assert usage.usage == 0x4321


def test_create_error():
    with pytest.raises(
        ValueError,
        match='You need to specify either the usage page and usage or the extended usage'
    ):
        hid_parser.Usage(0x1234, 0x4321, extended_usage=0x12344321)

    with pytest.raises(ValueError, match='No usage specified'):
        hid_parser.Usage()

    with pytest.raises(ValueError, match='No usage specified'):
        hid_parser.Usage(page=0x1234)

    with pytest.raises(ValueError, match='No usage specified'):
        hid_parser.Usage(usage=0x1234)


def test_int():
    assert int(hid_parser.Usage(0x1234, 0x4321)) == 0x12344321
    assert int(hid_parser.Usage(extended_usage=0x12344321)) == 0x12344321


def test_eq():
    assert hid_parser.Usage(0x1234, 0x4321) == hid_parser.Usage(0x1234, 0x4321)
    assert hid_parser.Usage(0x1234, 0x4321) == hid_parser.Usage(extended_usage=0x12344321)
    assert hid_parser.Usage(extended_usage=0x12344321) == hid_parser.Usage(0x1234, 0x4321)

    assert hid_parser.Usage(0x1234, 0x4321) != hid_parser.Usage(0x1234, 0x1234)
    assert hid_parser.Usage(0x1234, 0x4321) != []


def test_repr():
    assert repr(hid_parser.Usage(0x1234, 0x4321)) == 'Usage(page=0x1234, usage=0x4321)'
    assert repr(hid_parser.Usage(extended_usage=0x12344321)) == 'Usage(page=0x1234, usage=0x4321)'
    assert repr(hid_parser.Usage(0x0001, 0x0000)) == 'Usage(page=Generic Desktop Controls, usage=0x0000)'
    assert repr(hid_parser.Usage(0x0001, 0x0001)) == 'Usage(page=Generic Desktop Controls, usage=Pointer)'


def test_usage_types():
    assert hid_parser.Usage(0x0001, 0x0001).usage_types == (hid_parser.data.UsageTypes.CP,)
    assert hid_parser.Usage(0x0001, 0x0047).usage_types == (
        hid_parser.data.UsageTypes.DV,
        hid_parser.data.UsageTypes.DF,
    )
