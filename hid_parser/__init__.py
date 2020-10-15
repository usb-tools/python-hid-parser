# SPDX-License-Identifier: MIT

from __future__ import annotations  # noqa:F407

import functools
import struct
import sys

from typing import Any, Dict, Iterable, List, Optional, Sequence, TextIO, Tuple, Union


if sys.version_info >= (3, 8):
    from typing import Literal
else:  # pragma: no cover
    from typing_extensions import Literal

import hid_parser.data


__version__ = '0.0.2'


class Type():
    MAIN = 0
    GLOBAL = 1
    LOCAL = 2


class TagMain():
    INPUT = 0b1000
    OUTPUT = 0b1001
    FEATURE = 0b1011
    COLLECTION = 0b1010
    END_COLLECTION = 0b1100


class TagGlobal():
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


class TagLocal():
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


class BitNumber(int):
    def __init__(self, value: int):
        self._value = value

    def __int__(self) -> int:
        return self._value

    @property
    def byte(self) -> int:
        '''
        Number of bytes
        '''
        return self._value // 8

    @property
    def bit(self) -> int:
        '''
        Number of unaligned bits

        n.byte * 8 + n.bits = n
        '''
        if self.byte == 0:
            return self._value

        return self._value % self.byte

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


class Usage():
    def __init__(self, page: Optional[int], usage: Optional[int], *, extended_usage: Optional[int] = None) -> None:
        if extended_usage and page and usage:
            raise ValueError('You need to specify either the usage page and usage or the extended usage')
        if extended_usage is not None:
            self.page = extended_usage >> (2 * 8)
            self.usage = extended_usage & 0xffff
        elif page is not None and usage is not None:
            self.page = page
            self.usage = usage
        else:
            raise ValueError('No usage specified')

    def __int__(self) -> int:
        return self.page << (2 * 8) | self.usage

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.page == other.page and self.usage == other.usage

    def __repr__(self) -> str:
        try:
            page_str = hid_parser.data.UsagePages.get_description(self.page)
        except KeyError:
            page_str = f'0x{self.page:04x}'
        else:
            try:
                page = hid_parser.data.UsagePages.get_subdata(self.page)
                usage_str = page.get_description(self.usage)
            except (KeyError, ValueError):
                usage_str = f'0x{self.usage:04x}'
        return f'Usage(page={page_str}, usage={usage_str})'

    @property
    def usage_type(self) -> hid_parser.data.UsageTypes:
        typ = hid_parser.data.Collections.get_subdata(self.page).get_subdata(self.usage)

        if not isinstance(typ, hid_parser.data.UsageTypes):
            raise ValueError(f"Expecting UsageType but got '{type(typ)}'")

        return typ


class BaseItem():
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
        physical_min: Optional[int] = None,
        physical_max: Optional[int] = None,
    ):
        self._offset = BitNumber(offset)
        self._size = BitNumber(size)
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
    def physical_min(self) -> Optional[int]:
        return self._physical_min

    @property
    def physical_max(self) -> Optional[int]:
        return self._physical_max

    # flags

    @property
    def constant(self) -> bool:
        return self._flags & (0 << 0) == 1

    @property
    def data(self) -> bool:
        return self._flags & (0 << 0) == 0

    @property
    def relative(self) -> bool:
        return self._flags & (0 << 2) == 1

    @property
    def absolute(self) -> bool:
        return self._flags & (0 << 2) == 0


class VariableItem(MainItem):
    def __init__(
        self,
        offset: int,
        size: int,
        flags: int,
        usage: Usage,
        logical_min: int,
        logical_max: int,
        physical_min: Optional[int] = None,
        physical_max: Optional[int] = None,
    ):
        super().__init__(offset, size, flags, logical_min, logical_max, physical_min, physical_max)
        self._usage = usage

    def __repr__(self) -> str:
        return f'VariableItem(offset={self.offset}, size={self.size}, usage={self.usage})'

    @property
    def usage(self) -> Usage:
        return self._usage

    # flags (variable only, see HID spec 1.11 page 32)

    @property
    def wrap(self) -> bool:
        return self._flags & (0 << 3) == 1

    @property
    def linear(self) -> bool:
        return self._flags & (0 << 4) == 1

    @property
    def preferred_state(self) -> bool:
        return self._flags & (0 << 5) == 1

    @property
    def null_state(self) -> bool:
        return self._flags & (0 << 6) == 1

    @property
    def buffered_bytes(self) -> bool:
        return self._flags & (0 << 7) == 1

    @property
    def bitfield(self) -> bool:
        return self._flags & (0 << 7) == 0


class ArrayItem(MainItem):
    def __init__(
        self,
        offset: int,
        size: int,
        flags: int,
        usages: List[Usage],
        logical_min: int,
        logical_max: int,
        physical_min: Optional[int] = None,
        physical_max: Optional[int] = None,
    ):
        super().__init__(offset, size, flags, logical_min, logical_max, physical_min, physical_max)
        self._usages = usages

    @property
    def usages(self) -> List[Usage]:
        return self._usages


class InvalidReportDescriptor(Exception):
    pass


# report ID (None for no report ID), item list
_ITEM_POOL = Dict[Optional[int], List[BaseItem]]


class ReportDescriptor():
    def __init__(self, data: Sequence[int]) -> None:
        self._data = data

        self._input: _ITEM_POOL = {}
        self._output: _ITEM_POOL = {}
        self._feature: _ITEM_POOL = {}

        self.__offset: Dict[Optional[int], int] = {}

        self._parse()

    @property
    def data(self) -> Sequence[int]:
        return self._data

    def get_input_items(self, report_id: Optional[int] = None) -> List[BaseItem]:
        return self._input[report_id]

    @functools.lru_cache(maxsize=16)
    def get_input_report_size(self, report_id: Optional[int] = None) -> BitNumber:
        size = 0
        for item in self.get_input_items(report_id):
            size += item.size
        return BitNumber(size)

    def get_output_items(self, report_id: Optional[int] = None) -> List[BaseItem]:
        return self._output[report_id]

    @functools.lru_cache(maxsize=16)
    def get_output_report_size(self, report_id: Optional[int] = None) -> BitNumber:
        size = 0
        for item in self.get_output_items(report_id):
            size += item.size
        return BitNumber(size)

    def get_feature_items(self, report_id: Optional[int] = None) -> List[BaseItem]:
        return self._feature[report_id]

    @functools.lru_cache(maxsize=16)
    def get_feature_report_size(self, report_id: Optional[int] = None) -> BitNumber:
        size = 0
        for item in self.get_feature_items(report_id):
            size += item.size
        return BitNumber(size)

    def _iterate_raw(self) -> Iterable[Tuple[int, int, Optional[int]]]:
        i = 0
        while i < len(self.data):
            prefix = self.data[i]
            tag = (prefix & 0b11110000) >> 4
            typ = (prefix & 0b00001100) >> 2
            size = prefix & 0b00000011

            if size == 3:  # 6.2.2.2
                size = 4

            if size == 0:
                data = None
            elif size == 1:
                data = self.data[i+1]
            else:
                data = struct.unpack('<H', bytes(self.data[i+1:i+1+size]))[0]

            yield typ, tag, data

            i += size + 1

    def _append_item(self, pool: _ITEM_POOL, report_id: Optional[int], item: BaseItem) -> None:
        self.__offset[report_id] += item.size
        if report_id in pool:
            pool[report_id].append(item)
        else:
            pool[report_id] = [item]

    def _append_items(
        self,
        pool: _ITEM_POOL,
        report_id: Optional[int],
        report_count: int,
        report_size: int,
        usages: List[Usage],
        flags: int,
        data: Dict[str, Any],
    ) -> None:
        item: BaseItem
        is_array = flags & (1 << 1) == 0  # otherwise variable

        if is_array:
            for _ in range(report_count):
                item = ArrayItem(
                    offset=self.__offset[report_id],
                    size=report_size,
                    usages=usages,
                    flags=flags,
                    **data,
                )
                self._append_item(pool, report_id, item)
        else:
            '''
            HID 1.11, 6.2.2.9 says reports can be byte aligned by declaring a
            main item without usage. A main item can have multiple usages, as I
            interpret it, items are only considered padding when they have NO
            usages.
            '''
            if len(usages) == 0:
                for _ in range(report_count):
                    item = PaddingItem(self.__offset[report_id], report_size)
                    self._append_item(pool, report_id, item)
                return

            elif len(usages) != report_count:
                raise InvalidReportDescriptor(f'Expecting {report_count} usages but got {len(usages)}')

            for usage in usages:
                item = VariableItem(
                    offset=self.__offset[report_id],
                    size=report_size,
                    usage=usage,
                    flags=flags,
                    **data,
                )
                self._append_item(pool, report_id, item)

    def _parse(self, level: int = 0, file: TextIO = sys.stdout) -> None:  # noqa: C901
        self.__offset = {
            None: 0,
        }
        report_id: Optional[int] = None
        report_count: Optional[int] = None
        report_size: Optional[int] = None
        usage_page: Optional[int] = None
        usages: List[Usage] = []
        usage_min: Optional[int] = None
        glob: Dict[str, Any] = {}
        local: Dict[str, Any] = {}

        for typ, tag, data in self._iterate_raw():

            if typ == Type.MAIN:

                if tag in (TagMain.COLLECTION, TagMain.END_COLLECTION):
                    usages = []

                # we only care about input, output and features for now
                if tag not in (TagMain.INPUT, TagMain.OUTPUT, TagMain.FEATURE):
                    continue

                if report_count is None:
                    raise InvalidReportDescriptor('Trying to append an item but no report count given')
                if report_size is None:
                    raise InvalidReportDescriptor('Trying to append an item but no report size given')

                if tag == TagMain.INPUT:
                    if data is None:
                        raise InvalidReportDescriptor('Invalid input item')
                    self._append_items(
                        self._input,
                        report_id,
                        report_count,
                        report_size,
                        usages,
                        data,
                        {**glob, **local}
                    )

                elif tag == TagMain.OUTPUT:
                    if data is None:
                        raise InvalidReportDescriptor('Invalid output item')
                    self._append_items(
                        self._output,
                        report_id,
                        report_count,
                        report_size,
                        usages,
                        data,
                        {**glob, **local}
                    )

                elif tag == TagMain.FEATURE:
                    if data is None:
                        raise InvalidReportDescriptor('Invalid feature item')
                    self._append_items(
                        self._feature,
                        report_id,
                        report_count,
                        report_size,
                        usages,
                        data,
                        {**glob, **local}
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
                        raise InvalidReportDescriptor('Tried to set a report ID in a report that does not use them')
                    report_id = data
                    # initialize the item offset for this report ID
                    if report_id not in self.__offset:
                        self.__offset[report_id] = 0

                elif tag == TagGlobal.REPORT_COUNT:
                    report_count = data

                else:
                    raise NotImplementedError(f'Unsupported global tag: {bin(tag)}')

            elif typ == Type.LOCAL:

                if tag == TagLocal.USAGE:
                    if usage_page is None:
                        raise InvalidReportDescriptor('Usage field found but no usage page')
                    usages.append(Usage(usage_page, data))

                elif tag == TagLocal.USAGE_MINIMUM:
                    usage_min = data

                elif tag == TagLocal.USAGE_MAXIMUM:
                    if usage_min is None:
                        raise InvalidReportDescriptor('Usage maximum set but no usage minimum')
                    if data is None:
                        raise InvalidReportDescriptor('Invalid usage maximum value')
                    for i in range(usage_min, data + 1):
                        usages.append(Usage(usage_page, i))
                    usage_min = None

                else:
                    raise NotImplementedError(f'Unsupported global tag: {bin(tag)}')

    @staticmethod
    def _get_main_item_desc(value: int) -> str:
        return ', '.join([
            'Constant' if value & (1 << 0) else 'Data',
            'Variable' if value & (1 << 1) else 'Array',
            'Relative' if value & (1 << 2) else 'Absolute',
            'Wrap' if value & (1 << 3) else 'No Wrap',
            'Non Linear' if value & (1 << 4) else 'Linear',
            'No Preferred State' if value & (1 << 5) else 'Preferred State',
            'Null State' if value & (1 << 6) else 'No Null position',
            'Buffered Bytes' if value & (1 << 8) else 'Bit Field',
        ])

    def print(self, level: int = 0, file: TextIO = sys.stdout) -> None:  # noqa: C901
        def printl(string: str) -> None:
            print(' ' * level + string, file=file)

        usage_data: Union[Literal[False], Optional[hid_parser.data._Data]] = False

        for typ, tag, data in self._iterate_raw():
            if typ == Type.MAIN:

                if tag == TagMain.INPUT:
                    if data is None:
                        raise InvalidReportDescriptor('Invalid input item')
                    printl(f'Input ({self._get_main_item_desc(data)})')

                elif tag == TagMain.OUTPUT:
                    if data is None:
                        raise InvalidReportDescriptor('Invalid output item')
                    printl(f'Output ({self._get_main_item_desc(data)})')

                elif tag == TagMain.FEATURE:
                    if data is None:
                        raise InvalidReportDescriptor('Invalid feature item')
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
                            usage_data = hid_parser.data.UsagePages.get_subdata(data)
                        except ValueError:
                            usage_data = None
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
                    if usage_data is False:
                        raise InvalidReportDescriptor('Usage field found but no usage page')

                    if usage_data:
                        try:
                            printl(f'Usage ({usage_data.get_description(data)})')
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
