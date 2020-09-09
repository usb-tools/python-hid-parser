# SPDX-License-Identifier: MIT

from typing import Any, Dict, List, Optional, Tuple


class _DataMeta(type):
    '''
    This metaclass populates _desc and _ranges, following the structure described bellow

    The class should declare data as follows

        MY_DATA_VALUE = 0x01, 'Data description'

    or, for ranges,

        MY_DATA_RANGE = 0x02, ..., 0x06, 'Data range description'

    _desc and _ranges will then be populated with

        _desc[0x01] = 'Data description'
        _ranges.append(tuple(0x02, 0x06, 'Data range description'))

    It also does some verification to prevent duplicated data
    '''
    def __new__(mcs, name: str, bases: Tuple[Any], dic: Dict[str, Any]):  # type: ignore  # noqa: C901
        dic['_desc'] = {}
        dic['_ranges'] = []

        for attr in dic:
            if not attr.startswith('_') and isinstance(dic[attr], tuple):
                if len(dic[attr]) == 2:
                    num, desc = dic[attr]

                    if not isinstance(num, int):
                        raise TypeError(f"First element of '{attr}' should be an int")
                    if not isinstance(desc, str):
                        raise TypeError(f"Second element of '{attr}' should be an int")

                    if num in dic['_desc']:
                        raise ValueError(f"Duplicated value in '{attr}' ({num})")

                    dic[attr] = num
                    dic['_desc'][num] = desc
                elif len(dic[attr]) == 4:
                    nmin, el, nmax, desc = dic[attr]

                    if not el == Ellipsis:
                        raise TypeError(f"Second element of '{attr}' should be an ellipsis (...)")
                    if not isinstance(nmin, int):
                        raise TypeError(f"First element of '{attr}' should be an int")
                    if not isinstance(nmax, int):
                        raise TypeError(f"Third element of '{attr}' should be an int")
                    if not isinstance(desc, str):
                        raise TypeError(f"Fourth element of '{attr}' should be an int")

                    for num in dic['_desc']:
                        if nmin <= num <= nmax:
                            raise ValueError(f"Duplicated value in '{attr}' ({num})")

                    dic['_ranges'].append((nmin, nmax, desc))

        return super().__new__(mcs, name, bases, dic)


class _Data(metaclass=_DataMeta):
    '''
    This class provides a get_description method to get data out of _desc and _ranges.
    See the _DataMeta documentation for more information.
    '''
    _desc: Dict[int, str]
    _ranges: List[Tuple[int, int, str]]

    @classmethod
    def get_description(cls, num: Optional[int]) -> str:
        if num is None:
            raise KeyError('Value is not an int')

        if num in cls._desc:
            return cls._desc[num]

        for nmin, nmax, desc in cls._ranges:
            if nmin <= num <= nmax:
                return desc

        raise KeyError('Value not found')


class UsagePages(_Data):
    GENERIC_DESKTOP_CONTROLS_PAGE = 0x01, 'Generic Desktop Controls'
    SIMULATION_CONTROLS_PAGE = 0x02, 'Simulation Controls'
    VR_CONTROLS_PAGE = 0x03, 'VR Controls'
    SPORT_CONTROLS_PAGE = 0x04, 'Sport Controls'
    GAME_CONTROLS_PAGE = 0x05, 'Game Controls'
    GENERIC_DEVICE_CONTROLS_PAGE = 0x06, 'Generic Device Controls'
    KEYBOARD_KEYPAD_PAGE = 0x07, 'Keyboard/Keypad'
    LED_PAGE = 0x08, 'LED'
    BUTTON_PAGE = 0x09, 'Button'
    ORDINAL_PAGE = 0x0A, 'Ordinal'
    TELEPHONY_PAGE = 0x0B, 'Telephony'
    CONSUMER_PAGE = 0x0C, 'Consumer'
    DIGITIZER_PAGE = 0x0D, 'Digitizer'
    HAPTICS_PAGE = 0x0E, 'Haptics'
    PID_PAGE = 0x0F, 'PID'
    UNICODE_PAGE = 0x10, 'Unicode'
    EYE_AND_HEAD_TRACKER_PAGE = 0x12, 'Eye and Head Tracker'
    ALPHANUMERIC_DISPLAY_PAGE = 0x14, 'Alphanumeric Display'
    SENSOR_PAGE = 0x20, 'Sensor'
    MEDICAL_INSTRUMENTS_PAGE = 0x40, 'Medical Instruments'
    BRAILLE_DISPLAY_PAGE = 0x41, 'Braillie'
    LIGHTING_AND_ILLUMINATION_PAGE = 0x59, 'Lighting and Illumination'
    USB_MONITOR_PAGE = 0x80, 'USB Monitor'
    USB_ENUMERATED_VALUES_PAGE = 0x81, 'USB Enumerated Values'
    VESA_VIRTUAL_CONTROLS_PAGE = 0x82, 'VESA Virtual Controls'
    POWER_DEVICE_PAGE = 0x84, 'Power Device'
    BATTERY_SYSTEM_PAGE = 0x85, 'Battery System'
    BARCODE_SCANNER_PAGE = 0x8C, 'Barcode Scanner'
    WEIGHING_PAGE = 0x8D, 'Weighing'
    MSR_PAGE = 0x8E, 'MSR'
    RESERVED_POS_PAGE = 0x8F, 'Reserved POS'
    CAMERA_CONTROL_PAGE = 0x90, 'Camera Control'
    ARCADE_PAGE = 0x91, 'Arcade'
    GAMING_DEVICE_PAGE = 0x92, 'Gaming Device'
    FIDO_ALLIANCE_PAGE = 0xF1D0, 'FIDO Alliance'
    VENDOR_PAGE = 0xFF00, ..., 0xFFFF, 'Vendor Page'
