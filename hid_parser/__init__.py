# SPDX-License-Identifier: MIT

from __future__ import annotations

import struct
import sys
import textwrap
import typing
import warnings

from collections.abc import Collection, Iterable, Iterator, Sequence
from typing import Any, Literal, Optional, TextIO

import hid_parser.data


__version__ = '0.1.0'


class HIDWarning(Warning):
    pass


class HIDComplianceWarning(HIDWarning):
    pass


class HIDReportWarning(HIDWarning):
    pass


class HIDUnsupportedWarning(HIDWarning):
    pass


class Type:
    MAIN = 0
    GLOBAL = 1
    LOCAL = 2


class TagMain:
    INPUT = 0b1000
    OUTPUT = 0b1001
    FEATURE = 0b1011
    COLLECTION = 0b1010
    END_COLLECTION = 0b1100


class TagGlobal:
    USAGE_PAGE = 0b0000
    LOGICAL_MINIMUM = 0b0001
    LOGICAL_MAXIMUM = 0b0010
    PHYSICAL_MINIMUM = 0b0011
    PHYSICAL_MAXIMUM = 0b0100
    UNIT_EXPONENT = 0b0101
    UNIT = 0b0110
    REPORT_SIZE = 0b0111
    REPORT_ID = 0b1000
    REPORT_COUNT = 0b1001
    PUSH = 0b1010
    POP = 0b1011
    # These tags have signed integer data
    _signed_tags = (
        LOGICAL_MINIMUM,
        LOGICAL_MAXIMUM,
        PHYSICAL_MINIMUM,
        PHYSICAL_MAXIMUM,
        UNIT_EXPONENT,
    )


class TagLocal:
    USAGE = 0b0000
    USAGE_MINIMUM = 0b0001
    USAGE_MAXIMUM = 0b0010
    DESIGNATOR_INDEX = 0b0011
    DESIGNATOR_MINIMUM = 0b0100
    DESIGNATOR_MAXIMUM = 0b0101
    STRING_INDEX = 0b0111
    STRING_MINIMUM = 0b1000
    STRING_MAXIMUM = 0b1001
    DELIMITER = 0b1010


def _item_is_signed(tag: int, typ: int) -> bool:
    if typ != Type.GLOBAL:
        return False
    if tag in TagGlobal._signed_tags:
        return True
    else:
        return False


def _data_bit_shift(data: Sequence[int], offset: int, length: int) -> Sequence[int]:
    if not length > 0:
        msg = f'Invalid specified length: {length}'
        raise ValueError(msg)

    left_extra = offset % 8
    right_extra = 8 - (offset + length) % 8
    start_offset = offset // 8
    end_offset = (offset + length - 1) // 8
    byte_length = (length - 1) // 8 + 1

    if not end_offset < len(data):
        msg = f'Invalid data length: {len(data)} (expecting {end_offset + 1})'
        raise ValueError(msg)

    shifted = [0] * byte_length

    if right_extra == 8:
        right_extra = 0

    i = end_offset
    shifted_offset = byte_length - 1
    while shifted_offset >= 0:
        shifted[shifted_offset] = data[i] >> right_extra

        if i - start_offset >= 0:
            shifted[shifted_offset] |= (data[i - 1] & (0xFF >> (8 - right_extra))) << (8 - right_extra)

        shifted_offset -= 1
        i -= 1

    shifted[0] &= 0xFF >> ((left_extra + right_extra) % 8)

    if not len(shifted) == byte_length:
        msg = 'Invalid data'
        raise ValueError(msg)

    return shifted


class BitNumber(int):
    def __init__(self, value: int):
        self._value = value

    def __int__(self) -> int:
        return self._value

    def __eq__(self, other: Any) -> bool:
        try:
            return self._value == int(other)
        except:  # noqa: E722
            return False

    @property
    def byte(self) -> int:
        """
        Number of bytes
        """
        return self._value // 8

    @property
    def bit(self) -> int:
        """
        Number of unaligned bits

        n.byte * 8 + n.bits = n
        """
        if self.byte == 0:
            return self._value

        return self._value % (self.byte * 8)

    @staticmethod
    def _param_repr(value: int, unit: str) -> str:
        if value != 1:
            unit += 's'
        return f'{value}{unit}'

    def __repr__(self) -> str:
        byte_str = self._param_repr(self.byte, 'byte')
        bit_str = self._param_repr(self.bit, 'bit')

        if self.byte == 0 and self.bit == 0:
            return bit_str

        parts = []
        if self.byte != 0:
            parts.append(byte_str)
        if self.bit != 0:
            parts.append(bit_str)

        return ' '.join(parts)


class Usage:
    def __init__(
        self,
        page: int | None = None,
        usage: int | None = None,
        *,
        extended_usage: int | None = None,
    ) -> None:
        if extended_usage and page and usage:
            msg = 'You need to specify either the usage page and usage or the extended usage'
            raise ValueError(msg)
        if extended_usage is not None:
            self.page = extended_usage >> (2 * 8)
            self.usage = extended_usage & 0xFFFF
        elif page is not None and usage is not None:
            self.page = page
            self.usage = usage
        else:
            msg = 'No usage specified'
            raise ValueError(msg)

    def __int__(self) -> int:
        return self.page << (2 * 8) | self.usage

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.page == other.page and self.usage == other.usage

    def __hash__(self) -> int:
        return self.usage << (2 * 8) + self.page

    def __repr__(self) -> str:
        try:
            page_str = hid_parser.data.UsagePages.get_description(self.page)
        except KeyError:
            page_str = f'0x{self.page:04x}'
            usage_str = f'0x{self.usage:04x}'
        else:
            try:
                page = hid_parser.data.UsagePages.get_subdata(self.page)
                usage_str = page.get_description(self.usage)
            except (KeyError, ValueError):
                usage_str = f'0x{self.usage:04x}'
        return f'Usage(page={page_str}, usage={usage_str})'

    @property
    def usage_types(self) -> Collection[hid_parser.data.UsageTypes]:
        usage_page = hid_parser.data.UsagePages.get_subdata(self.page)
        usage_types = usage_page.get_subdata(self.usage)

        if not isinstance(usage_types, Collection):
            usage_types = (usage_types,)

        return usage_types


class UsageValue:
    def __init__(self, item: MainItem, value: int):
        self._item = item
        self._value = value

    def __int__(self) -> int:
        return self.value

    def __repr__(self) -> str:
        return repr(self.value)

    @property
    def value(self) -> int | bool:
        return self._value

    @property
    def constant(self) -> bool:
        return self._item.constant

    @property
    def data(self) -> bool:
        return self._item.data

    @property
    def relative(self) -> bool:
        return self._item.relative

    @property
    def absolute(self) -> bool:
        return self._item.absolute


class VendorUsageValue(UsageValue):
    def __init__(
        self,
        item: MainItem,
        *,
        value: int | None = None,
        value_list: list[int] | None = None,
    ):
        self._item = item
        if value:
            self._list = [value]
        elif value_list:
            self._list = value_list
        else:
            self._list = []

    def __int__(self) -> int:
        return self.value

    def __iter__(self) -> Iterator[int]:
        return iter(self.list)

    @property
    def value(self) -> int | bool:
        return int.from_bytes(self._list, byteorder='little')

    @property
    def list(self) -> list[int]:
        return self._list


class BaseItem:
    def __init__(self, offset: int, size: int):
        self._offset = BitNumber(offset)
        self._size = BitNumber(size)

    @property
    def offset(self) -> BitNumber:
        return self._offset

    @property
    def size(self) -> BitNumber:
        return self._size

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(offset={self.offset}, size={self.size})'


class PaddingItem(BaseItem):
    pass


class MainItem(BaseItem):
    def __init__(
        self,
        offset: int,
        size: int,
        flags: int,
        logical_min: int,
        logical_max: int,
        physical_min: int | None = None,
        physical_max: int | None = None,
    ):
        super().__init__(offset, size)
        self._flags = flags
        self._logical_min = logical_min
        self._logical_max = logical_max
        self._physical_min = physical_min
        self._physical_max = physical_max
        # TODO: unit

    @property
    def offset(self) -> BitNumber:
        return self._offset

    @property
    def size(self) -> BitNumber:
        return self._size

    @property
    def logical_min(self) -> int:
        return self._logical_min

    @property
    def logical_max(self) -> int:
        return self._logical_max

    @property
    def physical_min(self) -> int | None:
        return self._physical_min

    @property
    def physical_max(self) -> int | None:
        return self._physical_max

    # flags

    @property
    def constant(self) -> bool:
        return self._flags & (1 << 0) != 0

    @property
    def data(self) -> bool:
        return self._flags & (1 << 0) == 0

    @property
    def relative(self) -> bool:
        return self._flags & (1 << 2) != 0

    @property
    def absolute(self) -> bool:
        return self._flags & (1 << 2) == 0


class VariableItem(MainItem):
    _INCOMPATIBLE_TYPES = (
        # array types
        hid_parser.data.UsageTypes.SELECTOR,
        # collection types
        hid_parser.data.UsageTypes.NAMED_ARRAY,
        hid_parser.data.UsageTypes.COLLECTION_APPLICATION,
        hid_parser.data.UsageTypes.COLLECTION_LOGICAL,
        hid_parser.data.UsageTypes.COLLECTION_PHYSICAL,
        hid_parser.data.UsageTypes.USAGE_SWITCH,
        hid_parser.data.UsageTypes.USAGE_MODIFIER,
    )

    def __init__(
        self,
        offset: int,
        size: int,
        flags: int,
        usage: Usage,
        logical_min: int,
        logical_max: int,
        physical_min: int | None = None,
        physical_max: int | None = None,
    ):
        super().__init__(offset, size, flags, logical_min, logical_max, physical_min, physical_max)
        self._usage = usage

        try:
            if all(usage_type in self._INCOMPATIBLE_TYPES for usage_type in usage.usage_types):
                warnings.warn(
                    HIDComplianceWarning(f'{usage} has no compatible usage types with a variable item'), stacklevel=2
                )
        except (KeyError, ValueError):
            pass

    def __repr__(self) -> str:
        return f'VariableItem(offset={self.offset}, size={self.size}, usage={self.usage})'

    def parse(self, data: Sequence[int]) -> UsageValue:
        data = _data_bit_shift(data, self.offset, self.size)

        if hid_parser.data.UsageTypes.LINEAR_CONTROL in self.usage.usage_types or any(
            usage_type in hid_parser.data.UsageTypesData and usage_type != hid_parser.data.UsageTypes.SELECTOR
            for usage_type in self.usage.usage_types
        ):  # int
            value = int.from_bytes(data, byteorder='little')
        elif (
            hid_parser.data.UsageTypes.ON_OFF_CONTROL in self.usage.usage_types
            and not self.preferred_state
            and self.logical_min == -1
            and self.logical_max == 1
        ):  # bool - -1 is false
            value = int.from_bytes(data, byteorder='little') == 1
        else:  # bool
            value = bool.from_bytes(data, byteorder='little')

        return UsageValue(self, value)

    @property
    def usage(self) -> Usage:
        return self._usage

    # flags (variable only, see HID spec 1.11 page 32)

    @property
    def wrap(self) -> bool:
        return self._flags & (1 << 3) != 0

    @property
    def linear(self) -> bool:
        return self._flags & (1 << 4) != 0

    @property
    def preferred_state(self) -> bool:
        return self._flags & (1 << 5) != 0

    @property
    def null_state(self) -> bool:
        return self._flags & (1 << 6) != 0

    @property
    def buffered_bytes(self) -> bool:
        return self._flags & (1 << 7) != 0

    @property
    def bitfield(self) -> bool:
        return self._flags & (1 << 7) == 0


class ArrayItem(MainItem):
    _INCOMPATIBLE_TYPES = (
        # variable types
        hid_parser.data.UsageTypes.LINEAR_CONTROL,
        hid_parser.data.UsageTypes.ON_OFF_CONTROL,
        hid_parser.data.UsageTypes.MOMENTARY_CONTROL,
        hid_parser.data.UsageTypes.ONE_SHOT_CONTROL,
        hid_parser.data.UsageTypes.RE_TRIGGER_CONTROL,
        hid_parser.data.UsageTypes.STATIC_VALUE,
        hid_parser.data.UsageTypes.STATIC_FLAG,
        hid_parser.data.UsageTypes.DYNAMIC_VALUE,
        hid_parser.data.UsageTypes.DYNAMIC_FLAG,
        # collection types
        hid_parser.data.UsageTypes.NAMED_ARRAY,
        hid_parser.data.UsageTypes.COLLECTION_APPLICATION,
        hid_parser.data.UsageTypes.COLLECTION_LOGICAL,
        hid_parser.data.UsageTypes.COLLECTION_PHYSICAL,
        hid_parser.data.UsageTypes.USAGE_SWITCH,
        hid_parser.data.UsageTypes.USAGE_MODIFIER,
    )
    _IGNORE_USAGE_VALUES = (
        (
            hid_parser.data.UsagePages.KEYBOARD_KEYPAD_PAGE,
            hid_parser.data.KeyboardKeypad.NO_EVENT,
        ),
    )

    def __init__(
        self,
        offset: int,
        size: int,
        count: int,
        flags: int,
        usages: list[Usage],
        logical_min: int,
        logical_max: int,
        physical_min: int | None = None,
        physical_max: int | None = None,
    ):
        super().__init__(offset, size, flags, logical_min, logical_max, physical_min, physical_max)
        self._count = count
        self._usages = usages
        self._page = self._usages[0].page if usages else None

        for usage in self._usages:
            if usage.page != self._page:
                msg = f'Mismatching usage page in usage: {usage} (expecting {self._usages[0]})'
                raise ValueError(msg)
            try:
                if all(usage_type in self._INCOMPATIBLE_TYPES for usage_type in usage.usage_types):
                    warnings.warn(
                        HIDComplianceWarning(f'{usage} has no compatible usage types with an array item'), stacklevel=2
                    )
            except (KeyError, ValueError):
                pass

        self._ignore_usages: list[Usage] = []
        for page, usage_id in self._IGNORE_USAGE_VALUES:
            assert isinstance(page, int) and isinstance(usage_id, int)
            self._ignore_usages.append(Usage(page, usage_id))

    def __repr__(self) -> str:
        return (
            textwrap.dedent("""
            ArrayItem(
                offset={}, size={}, count={},
                usages=[
                    {},
                ],
            )
        """)
            .strip()
            .format(
                self.offset,
                self.size,
                self.count,
                ',\n        '.join(repr(usage) for usage in self.usages),
            )
        )

    def parse(self, data: Sequence[int]) -> dict[Usage, UsageValue]:
        usage_values: dict[Usage, UsageValue] = {}

        for i in range(self.count):
            aligned_data = _data_bit_shift(data, self.offset + i * 8, self.size)
            usage = Usage(self._page, int.from_bytes(aligned_data, byteorder='little'))

            if usage in self._ignore_usages:
                continue

            # vendor usages don't have usage any standard type - just save the raw data
            if usage.page in hid_parser.data.UsagePages.VENDOR_PAGE:
                if usage not in usage_values:
                    usage_values[usage] = VendorUsageValue(
                        self,
                        value=int.from_bytes(aligned_data, byteorder='little'),
                    )
                typing.cast(VendorUsageValue, usage_values[usage]).list.append(
                    int.from_bytes(aligned_data, byteorder='little')
                )
                continue

            if usage in self._usages and all(
                usage_type not in self._INCOMPATIBLE_TYPES for usage_type in usage.usage_types
            ):
                usage_values[usage] = UsageValue(self, True)

        return usage_values

    @property
    def count(self) -> int:
        return self._count

    @property
    def usages(self) -> list[Usage]:
        return self._usages


class InvalidReportDescriptor(Exception):
    pass


# report ID (None for no report ID), item list
_ITEM_POOL = dict[Optional[int], list[BaseItem]]


class ReportDescriptor:
    def __init__(self, data: Sequence[int]) -> None:
        self._data = data

        for byte in data:
            if byte < 0 or byte > 255:
                msg = f'A report descriptor should be represented by a list of bytes: found value {byte}'
                raise InvalidReportDescriptor(msg)

        self._input: _ITEM_POOL = {}
        self._output: _ITEM_POOL = {}
        self._feature: _ITEM_POOL = {}

        self._parse()

    @property
    def data(self) -> Sequence[int]:
        return self._data

    @property
    def input_report_ids(self) -> list[int | None]:
        return list(self._input.keys())

    @property
    def output_report_ids(self) -> list[int | None]:
        return list(self._output.keys())

    @property
    def feature_report_ids(self) -> list[int | None]:
        return list(self._feature.keys())

    def _get_report_size(self, items: list[BaseItem]) -> BitNumber:
        size = 0
        for item in items:
            if isinstance(item, ArrayItem):
                size += item.size * item.count
            else:
                size += item.size
        return BitNumber(size)

    def get_input_items(self, report_id: int | None = None) -> list[BaseItem]:
        return self._input[report_id]

    def get_input_report_size(self, report_id: int | None = None) -> BitNumber:
        return self._get_report_size(self.get_input_items(report_id))

    def get_output_items(self, report_id: int | None = None) -> list[BaseItem]:
        return self._output[report_id]

    def get_output_report_size(self, report_id: int | None = None) -> BitNumber:
        return self._get_report_size(self.get_output_items(report_id))

    def get_feature_items(self, report_id: int | None = None) -> list[BaseItem]:
        return self._feature[report_id]

    def get_feature_report_size(self, report_id: int | None = None) -> BitNumber:
        return self._get_report_size(self.get_feature_items(report_id))

    def _parse_report_items(self, items: list[BaseItem], data: Sequence[int]) -> dict[Usage, UsageValue]:
        parsed: dict[Usage, UsageValue] = {}
        for item in items:
            if isinstance(item, VariableItem):
                parsed[item.usage] = item.parse(data)
            elif isinstance(item, ArrayItem):
                usage_values = item.parse(data)
                for usage in usage_values:
                    if usage in parsed:
                        warnings.warn(HIDReportWarning(f'Overriding usage: {usage}'), stacklevel=2)
                parsed.update(usage_values)
            elif isinstance(item, PaddingItem):
                pass
            else:
                msg = f'Unknown item: {item}'
                raise TypeError(msg)
        return parsed

    def _parse_report(self, item_poll: _ITEM_POOL, data: Sequence[int]) -> dict[Usage, UsageValue]:
        if None in item_poll:  # unnumbered reports
            return self._parse_report_items(item_poll[None], data)
        else:  # numbered reports
            return self._parse_report_items(item_poll[data[0]], data[1:])

    def parse_input_report(self, data: Sequence[int]) -> dict[Usage, UsageValue]:
        return self._parse_report(self._input, data)

    def parse_output_report(self, data: Sequence[int]) -> dict[Usage, UsageValue]:
        return self._parse_report(self._output, data)

    def parse_feature_report(self, data: Sequence[int]) -> dict[Usage, UsageValue]:
        return self._parse_report(self._feature, data)

    def _iterate_raw(self) -> Iterable[tuple[int, int, int | None]]:
        i = 0
        while i < len(self.data):
            prefix = self.data[i]
            i += 1
            tag = (prefix & 0b11110000) >> 4
            typ = (prefix & 0b00001100) >> 2
            size = prefix & 0b00000011

            if size == 0:
                # 6.2.2.4 Main items with empty data have a value of zero
                if typ == Type.MAIN:
                    data = 0
                else:
                    data = None
            elif size > 3:
                msg = f'Invalid item size: {size}'
                raise ValueError(msg)
            else:
                # Pick an unpack format letter by size and signedness
                # Per 6.2.2.2, size of 0b11 means 4
                if _item_is_signed(tag, typ):
                    pack_type = '0bhl'[size]
                else:
                    pack_type = '0BHL'[size]
                fmt = f'<{pack_type}'
                size = struct.calcsize(fmt)
                if i + size > len(self.data):
                    msg = f'Invalid size: expecting >={i + size}, got {len(self.data)}'
                    raise InvalidReportDescriptor(msg)

                (data,) = struct.unpack(fmt, bytes(self.data[i : i + size]))

            yield typ, tag, data

            i += size

    def _append_item(
        self,
        offset_list: dict[int | None, int],
        pool: _ITEM_POOL,
        report_id: int | None,
        item: BaseItem,
    ) -> None:
        offset_list[report_id] += item.size
        if report_id in pool:
            pool[report_id].append(item)
        else:
            pool[report_id] = [item]

    def _append_items(
        self,
        offset_list: dict[int | None, int],
        pool: _ITEM_POOL,
        report_id: int | None,
        report_count: int,
        report_size: int,
        usages: list[Usage],
        flags: int,
        data: dict[str, Any],
    ) -> None:
        item: BaseItem
        is_array = flags & (1 << 1) == 0  # otherwise variable

        """
        HID 1.11, 6.2.2.9 says reports can be byte aligned by declaring a
        main item without usage. A main item can have multiple usages, as I
        interpret it, items are only considered padding when they have NO
        usages.
        """
        if len(usages) == 0 or not usages:
            for _ in range(report_count):
                item = PaddingItem(offset_list[report_id], report_size)
                self._append_item(offset_list, pool, report_id, item)
            return

        if is_array:
            item = ArrayItem(
                offset=offset_list[report_id],
                size=report_size,
                usages=usages,
                count=report_count,
                flags=flags,
                **data,
            )
            self._append_item(offset_list, pool, report_id, item)
        else:
            if len(usages) != report_count:
                error_str = f'Expecting {report_count} usages but got {len(usages)}'
                warnings.warn(HIDComplianceWarning(error_str), stacklevel=2)
                if len(usages) > report_count:
                    report_count = len(usages)
                else:
                    missing_usage_count = report_count - len(usages)
                    usages += [] * missing_usage_count

            for usage in usages:
                item = VariableItem(
                    offset=offset_list[report_id],
                    size=report_size,
                    usage=usage,
                    flags=flags,
                    **data,
                )
                self._append_item(offset_list, pool, report_id, item)

    def _parse(self, level: int = 0, file: TextIO = sys.stdout) -> None:  # noqa: C901
        offset_input: dict[int | None, int] = {
            None: 0,
        }
        offset_output: dict[int | None, int] = {
            None: 0,
        }
        offset_feature: dict[int | None, int] = {
            None: 0,
        }
        report_id: int | None = None
        report_count: int | None = None
        report_size: int | None = None
        usage_page: int | None = None
        usages: list[Usage] = []
        usage_min: int | None = None
        glob: dict[str, Any] = {}
        local: dict[str, Any] = {}

        for typ, tag, data in self._iterate_raw():
            if typ == Type.MAIN:
                if tag in (TagMain.COLLECTION, TagMain.END_COLLECTION):
                    usages = []

                # we only care about input, output and features for now
                if tag not in (TagMain.INPUT, TagMain.OUTPUT, TagMain.FEATURE):
                    continue

                if report_count is None:
                    msg = 'Trying to append an item but no report count given'
                    raise InvalidReportDescriptor(msg)
                if report_size is None:
                    msg = 'Trying to append an item but no report size given'
                    raise InvalidReportDescriptor(msg)

                if tag == TagMain.INPUT:
                    if data is None:
                        msg = 'Invalid input item'
                        raise InvalidReportDescriptor(msg)
                    self._append_items(
                        offset_input,
                        self._input,
                        report_id,
                        report_count,
                        report_size,
                        usages,
                        data,
                        {**glob, **local},
                    )

                elif tag == TagMain.OUTPUT:
                    if data is None:
                        msg = 'Invalid output item'
                        raise InvalidReportDescriptor(msg)
                    self._append_items(
                        offset_output,
                        self._output,
                        report_id,
                        report_count,
                        report_size,
                        usages,
                        data,
                        {**glob, **local},
                    )

                elif tag == TagMain.FEATURE:
                    if data is None:
                        msg = 'Invalid feature item'
                        raise InvalidReportDescriptor(msg)
                    self._append_items(
                        offset_feature,
                        self._feature,
                        report_id,
                        report_count,
                        report_size,
                        usages,
                        data,
                        {**glob, **local},
                    )

                # clear local
                usages = []
                usage_min = None
                local = {}

                # we don't care about collections for now, maybe in the future...

            elif typ == Type.GLOBAL:
                if tag == TagGlobal.USAGE_PAGE:
                    usage_page = data

                elif tag == TagGlobal.LOGICAL_MINIMUM:
                    glob['logical_min'] = data

                elif tag == TagGlobal.LOGICAL_MAXIMUM:
                    glob['logical_max'] = data

                elif tag == TagGlobal.PHYSICAL_MINIMUM:
                    glob['physical_min'] = data

                elif tag == TagGlobal.PHYSICAL_MAXIMUM:
                    glob['physical_max'] = data

                elif tag == TagGlobal.REPORT_SIZE:
                    report_size = data

                elif tag == TagGlobal.REPORT_ID:
                    if not report_id and (self._input or self._output or self._feature):
                        msg = 'Tried to set a report ID in a report that does not use them'
                        raise InvalidReportDescriptor(msg)
                    report_id = data
                    # initialize the item offset for this report ID
                    for offset_list in (offset_input, offset_output, offset_feature):
                        if report_id not in offset_list:
                            offset_list[report_id] = 0

                elif tag in (TagGlobal.UNIT, TagGlobal.UNIT_EXPONENT):
                    warnings.warn(
                        HIDUnsupportedWarning("Data specifies a unit or unit exponent, but we don't support those yet"),
                        stacklevel=2,
                    )

                elif tag == TagGlobal.REPORT_COUNT:
                    report_count = data

                else:
                    msg = f'Unsupported global tag: {bin(tag)}'
                    raise NotImplementedError(msg)

            elif typ == Type.LOCAL:
                if tag == TagLocal.USAGE:
                    if usage_page is None:
                        msg = 'Usage field found but no usage page'
                        raise InvalidReportDescriptor(msg)
                    usages.append(Usage(usage_page, data))

                elif tag == TagLocal.USAGE_MINIMUM:
                    usage_min = data

                elif tag == TagLocal.USAGE_MAXIMUM:
                    if usage_min is None:
                        msg = 'Usage maximum set but no usage minimum'
                        raise InvalidReportDescriptor(msg)
                    if data is None:
                        msg = 'Invalid usage maximum value'
                        raise InvalidReportDescriptor(msg)
                    for i in range(usage_min, data + 1):
                        usages.append(Usage(usage_page, i))
                    usage_min = None

                elif tag in (
                    TagLocal.STRING_INDEX,
                    TagLocal.STRING_MINIMUM,
                    TagLocal.STRING_MAXIMUM,
                ):
                    pass  # we don't care about this information to parse the reports

                else:
                    msg = f'Unsupported local tag: {bin(tag)}'
                    raise NotImplementedError(msg)

    @staticmethod
    def _get_main_item_desc(value: int) -> str:
        fields = [
            'Constant' if value & (1 << 0) else 'Data',
            'Variable' if value & (1 << 1) else 'Array',
            'Relative' if value & (1 << 2) else 'Absolute',
        ]
        if value & (1 << 1):
            # variable only
            fields += [
                'Wrap' if value & (1 << 3) else 'No Wrap',
                'Non Linear' if value & (1 << 4) else 'Linear',
                'No Preferred State' if value & (1 << 5) else 'Preferred State',
                'Null State' if value & (1 << 6) else 'No Null position',
                'Buffered Bytes' if value & (1 << 8) else 'Bit Field',
            ]
        return ', '.join(fields)

    def print(self, level: int = 0, file: TextIO = sys.stdout) -> None:  # noqa: C901
        def printl(string: str) -> None:
            print(' ' * level + string, file=file)

        usage_page: Literal[False] | hid_parser.data.UsagePage | None = False

        for typ, tag, data in self._iterate_raw():
            if typ == Type.MAIN:
                if tag == TagMain.INPUT:
                    if data is None:
                        msg = 'Invalid input item'
                        raise InvalidReportDescriptor(msg)
                    printl(f'Input ({self._get_main_item_desc(data)})')

                elif tag == TagMain.OUTPUT:
                    if data is None:
                        msg = 'Invalid output item'
                        raise InvalidReportDescriptor(msg)
                    printl(f'Output ({self._get_main_item_desc(data)})')

                elif tag == TagMain.FEATURE:
                    if data is None:
                        msg = 'Invalid feature item'
                        raise InvalidReportDescriptor(msg)
                    printl(f'Feature ({self._get_main_item_desc(data)})')

                elif tag == TagMain.COLLECTION:
                    printl(f'Collection ({hid_parser.data.Collections.get_description(data)})')
                    level += 1

                elif tag == TagMain.END_COLLECTION:
                    level -= 1
                    printl('End Collection')

            elif typ == Type.GLOBAL:
                if tag == TagGlobal.USAGE_PAGE:
                    try:
                        printl(f'Usage Page ({hid_parser.data.UsagePages.get_description(data)})')
                        try:
                            usage_page = hid_parser.data.UsagePages.get_subdata(data)
                        except ValueError:
                            usage_page = None
                    except KeyError:
                        printl(f'Usage Page (Unknown 0x{data:04x})')

                elif tag == TagGlobal.LOGICAL_MINIMUM:
                    printl(f'Logical Minimum ({data})')

                elif tag == TagGlobal.LOGICAL_MAXIMUM:
                    printl(f'Logical Maximum ({data})')

                elif tag == TagGlobal.PHYSICAL_MINIMUM:
                    printl(f'Physical Minimum ({data})')

                elif tag == TagGlobal.PHYSICAL_MAXIMUM:
                    printl(f'Physical Maximum ({data})')

                elif tag == TagGlobal.UNIT_EXPONENT:
                    printl(f'Unit Exponent (0x{data:04x})')

                elif tag == TagGlobal.UNIT:
                    printl(f'Unit (0x{data:04x})')

                elif tag == TagGlobal.REPORT_SIZE:
                    printl(f'Report Size ({data})')

                elif tag == TagGlobal.REPORT_ID:
                    printl(f'Report ID (0x{data:02x})')

                elif tag == TagGlobal.REPORT_COUNT:
                    printl(f'Report Count ({data})')

                elif tag == TagGlobal.PUSH:
                    printl(f'Push ({data})')

                elif tag == TagGlobal.POP:
                    printl(f'Pop ({data})')

            elif typ == Type.LOCAL:
                if tag == TagLocal.USAGE:
                    if usage_page is False:
                        msg = 'Usage field found but no usage page'
                        raise InvalidReportDescriptor(msg)

                    if usage_page:
                        try:
                            printl(f'Usage ({usage_page.get_description(data)})')
                        except KeyError:
                            printl(f'Usage (Unknown, 0x{data:04x})')
                    else:
                        printl(f'Usage (0x{data:04x})')

                elif tag == TagLocal.USAGE_MINIMUM:
                    printl(f'Usage Minimum ({data})')

                elif tag == TagLocal.USAGE_MAXIMUM:
                    printl(f'Usage Maximum ({data})')

                elif tag == TagLocal.DESIGNATOR_INDEX:
                    printl(f'Designator Index ({data})')

                elif tag == TagLocal.DESIGNATOR_MINIMUM:
                    printl(f'Designator Minimum ({data})')

                elif tag == TagLocal.DESIGNATOR_MAXIMUM:
                    printl(f'Designator Maximum ({data})')

                elif tag == TagLocal.STRING_INDEX:
                    printl(f'String Index ({data})')

                elif tag == TagLocal.STRING_MINIMUM:
                    printl(f'String Minimum ({data})')

                elif tag == TagLocal.STRING_MAXIMUM:
                    printl(f'String Maximum ({data})')

                elif tag == TagLocal.DELIMITER:
                    printl(f'Delemiter ({data})')
