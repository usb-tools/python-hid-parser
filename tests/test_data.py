# SPDX-License-Identifier: MIT

import re

import pytest

import hid_parser.data


def test_class():
    class Test1(hid_parser.data._Data):
        A = 0x00, 'Field A'
        B = 0x10, 'Field B'
        C = 0x20, 'Field C'

    class Test2(hid_parser.data._Data):
        A = 0x00, ..., 0x10, 'Field A'
        B = 0x11, 'Field B'
        C = 0x12, 'Field C'

    class Test3(hid_parser.data._Data):
        A = 0x00, 'Field A', 'some data'
        B = 0x10, 'Field B', 'some more data'
        C = 0x20, 'Field C', 'some even more data'

    class Test4(hid_parser.data._Data):
        A = 0x00, ..., 0x10, 'Field A', 'some data'
        B = 0x11, 'Field B'
        C = 0x12, 'Field C', 'some more data'

    Test1()
    Test2()
    Test3()
    Test4()


def test_class_single_error():
    with pytest.raises(TypeError, match="First element of 'A' should be an int"):
        class TestFirst(hid_parser.data._Data):
            A = 'test', 'Field A'

    with pytest.raises(TypeError, match="Second element of 'A' should be a string"):
        class TestSecond(hid_parser.data._Data):
            A = 0x00, 0x01

    with pytest.raises(ValueError, match=re.escape("Duplicated value in 'B' (0)")):
        class TestDuplicated(hid_parser.data._Data):
            A = 0x00, 'Field A'
            B = 0x00, 'Field B'


def test_class_range_error():
    with pytest.raises(ValueError, match='Invalid field: A'):
        class TestInvalid(hid_parser.data._Data):
            A = ()

    with pytest.raises(TypeError, match="Second element of 'A' should be an ellipsis (...)"):
        class TestEllipsis(hid_parser.data._Data):
            A = 0x00, 0x01, 0x02, 'Field A'

    with pytest.raises(TypeError, match="First element of 'A' should be an int"):
        class TestFirst(hid_parser.data._Data):
            A = 'test', ..., 0x00, 'Field A'

    with pytest.raises(TypeError, match="Third element of 'A' should be an int"):
        class TestThird(hid_parser.data._Data):
            A = 0x00, ..., 'test', 'Field A'

    with pytest.raises(TypeError, match="Fourth element of 'A' should be a string"):
        class TestFourth(hid_parser.data._Data):
            A = 0x00, ..., 0x01, 0x00

    with pytest.raises(ValueError, match=re.escape("Duplicated value in 'B' (5)")):
        class TestDuplicatedSingleFirst(hid_parser.data._Data):
            A = 0x05, 'Field A'
            B = 0x00, ..., 0x10, 'Field B'

    with pytest.raises(ValueError, match=re.escape("Duplicated value in 'B' (5)")):
        class TestDuplicatedRangeFirst(hid_parser.data._Data):
            A = 0x00, ..., 0x10, 'Field A'
            B = 0x05, 'Field B'


def test_description():
    class TestData(hid_parser.data._Data):
        A = 0, 'Field A'

    assert TestData().get_description(0) == 'Field A'


def test_subdata():
    class TestData(hid_parser.data._Data):
        A = 0, 'Field A', 'some data'

    assert TestData().get_subdata(0) == 'some data'


def test_range():
    class TestData(hid_parser.data._Data):
        A = 0x10, ..., 0x20, 'Field A'

    data = TestData()

    for i in range(0x10, 0x20):
        assert data.get_description(i) == 'Field A'

    with pytest.raises(KeyError, match='Data not found for index 0x09 in TestData'):
        data.get_subdata(0x09)
    with pytest.raises(KeyError, match='Data not found for index 0x21 in TestData'):
        data.get_subdata(0x21)


def test_data_dict():
    class TestData(hid_parser.data._Data):
        data = {
            'A': (0x00, 'Field A'),
            'B': (0x10, 'Field B'),
            'C': (0x20, 'Field C'),
        }

    data = TestData()

    assert data.A == TestData.A == 0x00
    assert data.B == TestData.B == 0x10
    assert data.C == TestData.C == 0x20
    assert data.get_description(0x00) == 'Field A'
    assert data.get_description(0x10) == 'Field B'
    assert data.get_description(0x20) == 'Field C'


def test_key_none():
    class TestData(hid_parser.data._Data):
        pass

    data = TestData()

    with pytest.raises(KeyError, match='Data index is not an int'):
        data.get_description(None)
    with pytest.raises(KeyError, match='Data index is not an int'):
        data.get_subdata(None)


def test_key_not_found():
    class TestData(hid_parser.data._Data):
        pass

    data = TestData()

    with pytest.raises(KeyError, match='Data not found for index 0x00 in TestData'):
        data.get_description(0)
    with pytest.raises(KeyError, match='Data not found for index 0x00 in TestData'):
        data.get_subdata(0)


def test_no_subdata():
    class TestData(hid_parser.data._Data):
        A = 0, 'Field A'

    data = TestData()

    with pytest.raises(ValueError, match='Sub-data not available'):
        data.get_subdata(0)
