# SPDX-License-Identifier: MIT

import struct
import sys

from typing import Iterable, Optional, Sequence, TextIO, Tuple, Union


if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

import hid_parser.data


__version__ = '0.0.1'


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
    def __init__(self, x: Union[int, str, bytes, bytearray], base: int = 10):
        super().__init__(x, base=base)  # type: ignore

    @property
    def byte(self) -> int:
        '''
        Convert number to bytes
        '''
        return self // 8

    @property
    def byte_offset(self) -> int:
        '''
        Number of unaligned bits

        n.byte * 8 + n.byte_offset = n
        '''
        return self % self.byte

    def __repr__(self) -> str:
        return f'(bytes={self.byte}, bit={self.byte_offset})'


class Usage():
    def __init__(self, page: Optional[int], usage: Optional[int], *, extended_usage: Optional[int]) -> None:
        if extended_usage and page and usage:
            raise ValueError('You need to specify either the usage page and usage or the extended usage')
        if extended_usage:
            self.page = extended_usage >> (2 * 8)
            self.usage = extended_usage & 0xffff
        elif page and usage:
            self.page = page
            self.usage = usage
        else:
            raise ValueError('No usage specified')

    def __int__(self) -> int:
        return self.page << (2 * 8) | self.usage


class Item():
    def __init__(self, offset: int, size: int, usage: Usage) -> None:
        self._offset = BitNumber(offset)
        self._size = BitNumber(size)
        self._usage = usage

    @property
    def offset(self) -> BitNumber:
        return self._offset

    @property
    def size(self) -> BitNumber:
        return self._size

    @property
    def usage(self) -> Usage:
        return self._usage


class InvalidReportDescriptor(Exception):
    pass


class ReportDescriptor():
    def __init__(self, data: Sequence[int]) -> None:
        self._data = data

    @property
    def data(self) -> Sequence[int]:
        return self._data

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

    @staticmethod
    def _get_main_item_desc(value: int) -> str:
        return ', '.join([
            'Constant' if value & (0 << 0) else 'Data',
            'Variable' if value & (0 << 1) else 'Array',
            'Relative' if value & (0 << 2) else 'Absolute',
            'Wrap' if value & (0 << 3) else 'No Wrap',
            'Non Linear' if value & (0 << 4) else 'Linear',
            'No Preferred State' if value & (0 << 5) else 'Preferred State',
            'Null State' if value & (0 << 6) else 'No Null position',
            'Buffered Bytes' if value & (0 << 8) else 'Bit Field',
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
