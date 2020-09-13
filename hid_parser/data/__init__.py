# SPDX-License-Identifier: MIT

from typing import Any, Dict, List, Optional, Tuple


class _DataMeta(type):
    '''
    This metaclass populates _single and _range, following the structure described bellow

    The class should declare data as follows

        MY_DATA_VALUE = 0x01, 'Data description'

    or, for ranges,

        MY_DATA_RANGE = 0x02, ..., 0x06, 'Data range description'

    _single and _range will then be populated with

        _single[0x01] = 'Data description'
        _range.append(tuple(0x02, 0x06, 'Data range description'))

    It also does some verification to prevent duplicated data
    '''
    def __new__(mcs, name: str, bases: Tuple[Any], dic: Dict[str, Any]):  # type: ignore  # noqa: C901
        dic['_single'] = {}
        dic['_range'] = []

        for attr in dic:
            if not attr.startswith('_') and isinstance(dic[attr], tuple):
                if len(dic[attr]) == 2 or len(dic[attr]) == 4:  # missing sub data
                    dic[attr] = dic[attr] + (None,)

                if len(dic[attr]) == 3:  # single
                    num, desc, sub = dic[attr]

                    if not isinstance(num, int):
                        raise TypeError(f"First element of '{attr}' should be an int")
                    if not isinstance(desc, str):
                        raise TypeError(f"Second element of '{attr}' should be an int")

                    if num in dic['_single']:
                        raise ValueError(f"Duplicated value in '{attr}' ({num})")

                    dic[attr] = num
                    dic['_single'][num] = desc, sub
                elif len(dic[attr]) == 5:  # range
                    nmin, el, nmax, desc, sub = dic[attr]

                    if not el == Ellipsis:
                        raise TypeError(f"Second element of '{attr}' should be an ellipsis (...)")
                    if not isinstance(nmin, int):
                        raise TypeError(f"First element of '{attr}' should be an int")
                    if not isinstance(nmax, int):
                        raise TypeError(f"Third element of '{attr}' should be an int")
                    if not isinstance(desc, str):
                        raise TypeError(f"Fourth element of '{attr}' should be an int")

                    for num in dic['_single']:
                        if nmin <= num <= nmax:
                            raise ValueError(f"Duplicated value in '{attr}' ({num})")

                    dic['_range'].append((nmin, nmax, (desc, sub)))

        return super().__new__(mcs, name, bases, dic)


class _Data(metaclass=_DataMeta):
    '''
    This class provides a get_description method to get data out of _single and _range.
    See the _DataMeta documentation for more information.
    '''
    _DATA = Tuple[str, Optional['_Data']]
    _single: Dict[int, _DATA]
    _range: List[Tuple[int, int, _DATA]]

    @classmethod
    def _get_data(cls, num: Optional[int]) -> _DATA:
        if num is None:
            raise KeyError('Value is not an int')

        if num in cls._single:
            return cls._single[num]

        for nmin, nmax, data in cls._range:
            if nmin <= num <= nmax:
                return data

        raise KeyError('Value not found')

    @classmethod
    def get_description(cls, num: Optional[int]) -> str:
        return cls._get_data(num)[0]

    @classmethod
    def get_subdata(cls, num: Optional[int]) -> '_Data':
        subdata = cls._get_data(num)[1]

        if not subdata:
            raise ValueError('Sub-data not available')

        return subdata


class Collections(_Data):
    PHYSICAL = 0x00, 'Physical'
    APPLICATION = 0x01, 'Application'
    LOGICAL = 0x02, 'Logical'
    REPORT = 0x03, 'Report'
    NAMED_ARRAY = 0x04, 'Named Array'
    USAGE_SWITCH = 0x05, 'Usage Switch'
    USAGE_MODIFIER = 0x06, 'Usage Modifier'
    VENDOR = 0x80, ..., 0xff, 'Vendor'


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
