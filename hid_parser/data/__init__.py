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

        MY_DATA_VALUE = 0x01
        _single[0x01] = ('Data description', None)
        _range.append(tuple(0x02, 0x06, ('Data range description', None)))

    As you can see, for single data insertions, the variable will be kept with
    the first value of the tuple. Both single and range data insertions will
    register the data into the correspondent data holders.

    You can also define subdata,

        MY_DATA_VALUE = 0x01, 'Data description', OTHER_DATA_TYPE
        MY_DATA_RANGE = 0x02, ..., 0x06, 'Data range description', YET_OTHER_DATA_TYPE

    Which will result in

        MY_DATA_VALUE = 0x01
        _single[0x01] = ('Data description', OTHER_DATA_TYPE)
        _range.append(tuple(0x02, 0x06, ('Data range description', YET_OTHER_DATA_TYPE)))

    This metaclass also does some verification to prevent duplicated data.
    '''
    def __new__(mcs, name: str, bases: Tuple[Any], dic: Dict[str, Any]):  # type: ignore  # noqa: C901
        dic['_single'] = {}
        dic['_range'] = []

        # allow constructing data via a data dictionary as opposed to directly in the object body
        if 'data' in dic:
            data = dic.pop('data')
        else:
            data = dic

        for attr in data:
            if not attr.startswith('_') and isinstance(data[attr], tuple):
                if len(data[attr]) == 2 or len(data[attr]) == 4:  # missing sub data
                    data[attr] = data[attr] + (None,)

                if len(data[attr]) == 3:  # single
                    num, desc, sub = data[attr]

                    if not isinstance(num, int):
                        raise TypeError(f"First element of '{attr}' should be an int")
                    if not isinstance(desc, str):
                        raise TypeError(f"Second element of '{attr}' should be an int")

                    if num in dic['_single']:
                        raise ValueError(f"Duplicated value in '{attr}' ({num})")

                    dic[attr] = num
                    dic['_single'][num] = desc, sub
                elif len(data[attr]) == 5:  # range
                    nmin, el, nmax, desc, sub = data[attr]

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


class GenericDesktopControls(_Data):
    POINTER = 0x01, 'Pointer'
    MOUSE = 0x02, 'Mouse'
    JOYSTICK = 0x04, 'Joystick'
    GAMEPAD = 0x05, 'Game Pad'
    KEYBOARD = 0x06, 'Keyboard'
    KEYPAD = 0x07, 'Keypad'
    MULTI_AXIS_CONTROLLER = 0x08, 'Multi-axis Controller'
    TABLET_PC_SYSTEM_CONTROLS = 0x09, 'Tablet PC System Controls'
    X = 0x30, 'X'
    Y = 0x31, 'Y'
    Z = 0x32, 'Z'
    RX = 0x33, 'Rx'
    RY = 0x34, 'Ry'
    RX = 0x35, 'Rz'
    SLIDER = 0x36, 'Slider'
    DIAL = 0x37, 'Dial'
    WHEEL = 0x38, 'Wheel'
    HAT_SWITCH = 0x39, 'Hat switch'
    COUNTED_BUFFER = 0x3A, 'Counted Buffer'
    BYTE_COUNT = 0x3B, 'Byte Count'
    MOTION_WAKEUP = 0x3C, 'Motion Wakeup'
    START = 0x3D, 'Start'
    SELECT = 0x3E, 'Select'
    VX = 0x40, 'Vx'
    VY = 0x41, 'Vy'
    VZ = 0x42, 'Vz'
    VBRX = 0x43, 'Vbrx'
    VBRY = 0x44, 'Vbry'
    VBRZ = 0x45, 'Vbrz'
    VNO = 0x46, 'Vno'
    FEATURE_NOTIFICATION = 0x47, 'Feature Notification'
    RESOLUTION_MULTIPLIER = 0x48, 'Resolution Multiplier'
    SYSTEM_CONTROL = 0x80, 'System Control'
    SYSTEM_POWER_CONTROL = 0x81, 'System Power Down'
    SYSTEM_SLEEP = 0x82, 'System Sleep'
    SYSTEM_WAKE_UP = 0x83, 'System Wake Up'
    SYSTEM_CONTEXT_MENU = 0x84, 'System Context Menu'
    SYSTEM_MAIN_MENU = 0x85, 'System Main Menu'
    SYSTEM_APP_MENU = 0x86, 'System App Menu'
    SYSTEM_MENU_HELP = 0x87, 'System Menu Help'
    SYSTEM_MENU_EXIT = 0x88, 'System Menu Exit'
    SYSTEM_MENU_SELECT = 0x89, 'System Menu Select'
    SYSTEM_MENU_RIGHT = 0x8A, 'System Menu Right'
    SYSTEM_MENU_LEFT = 0x8B, 'System Menu Left'
    SYSTEM_MENU_UP = 0x8C, 'System Menu Up'
    SYSTEM_MENU_DOWN = 0x8D, 'System Menu Down'
    SYSTEM_COLD_RESTART = 0x8E, 'System Cold Restart'
    SYSTEM_WARM_RESTART = 0x8F, 'System Warm Restart'
    DPAD_UP = 0x90, 'D-pad Up'
    DPAD_DOWN = 0x91, 'D-pad Down'
    DPAD_RIGHT = 0x92, 'D-pad Right'
    DPAD_LEFT = 0x93, 'D-pad Left'
    SYSTEM_DOCK = 0xA0, 'System Dock'
    SYSTEM_UNDOCK = 0xA1, 'System Undock'
    SYSTEM_SETUP = 0xA2, 'System Setup'
    SYSTEM_BREAK = 0xA3, 'System Break'
    SYSTEM_DEBBUGER_BREAK = 0xA4, 'System Debugger Break'
    APPLICATION_BREAK = 0xA5, 'Application Break'
    APPLICATION_DEBBUGER_BREAK = 0xA6, 'Application Debugger Break'
    SYSTEM_SPEAKER_MUTE = 0xA7, 'System Speaker Mute'
    SYSTEM_HIBERNATE = 0xA8, 'System Hibernate'
    SYSTEM_DISPLAY_INVERT = 0xB0, 'System Display Invert'
    SYSTEM_DISPLAY_INTERNAL = 0xB1, 'System Display Internal'
    SYSTEM_DISPLAY_EXTERNAL = 0xB2, 'System Display External'
    SYSTEM_DISPLAY_BOTH = 0xB3, 'System Display Both'
    SYSTEM_DISPLAY_DUAL = 0xB4, 'System Display Dual'
    SYSTEM_DISPLAY_TOGGLE = 0xB5, 'System Display Toggle Int/Ext'
    SYSTEM_DISPLAY_SWAP = 0xB6, 'System Display Swap Primary/Secondary'
    SYSTEM_DISPLAY_LCD_AUTOSCALE = 0xB7, 'System Display LCD Autoscale'


class Button(_Data):
    data = {
        'NO_BUTTON': (0x0000, 'Button 1 (primary/trigger)'),
        'BUTTON_1': (0x0001, 'Button 1 (primary/trigger)'),
        'BUTTON_2': (0x0002, 'Button 2 (secondary)'),
        'BUTTON_3': (0x0003, 'Button 3 (tertiary)'),
    }

    for _i in range(0x0004, 0xffff):
        data[f'BUTTON_{_i}'] = _i, f'Button {_i}'


class UsagePages(_Data):
    GENERIC_DESKTOP_CONTROLS_PAGE = 0x01, 'Generic Desktop Controls', GenericDesktopControls
    SIMULATION_CONTROLS_PAGE = 0x02, 'Simulation Controls'
    VR_CONTROLS_PAGE = 0x03, 'VR Controls'
    SPORT_CONTROLS_PAGE = 0x04, 'Sport Controls'
    GAME_CONTROLS_PAGE = 0x05, 'Game Controls'
    GENERIC_DEVICE_CONTROLS_PAGE = 0x06, 'Generic Device Controls'
    KEYBOARD_KEYPAD_PAGE = 0x07, 'Keyboard/Keypad'
    LED_PAGE = 0x08, 'LED'
    BUTTON_PAGE = 0x09, 'Button', Button
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
