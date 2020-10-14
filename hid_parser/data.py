# SPDX-License-Identifier: MIT

import enum

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
                        raise TypeError(f"Second element of '{attr}' should be a string")

                    if num in dic['_single']:
                        raise ValueError(f"Duplicated value in '{attr}' ({num})")

                    for nmin, nmax, _ in dic['_range']:
                        if nmin <= num <= nmax:
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
                        raise TypeError(f"Fourth element of '{attr}' should be a string")

                    for num in dic['_single']:
                        if nmin <= num <= nmax:
                            raise ValueError(f"Duplicated value in '{attr}' ({num})")

                    dic['_range'].append((nmin, nmax, (desc, sub)))

                else:
                    raise ValueError(f'Invalid field: {attr}')

        return super().__new__(mcs, name, bases, dic)


class _Data(metaclass=_DataMeta):
    '''
    This class provides a get_description method to get data out of _single and _range.
    See the _DataMeta documentation for more information.
    '''
    _DATA = Tuple[str, Optional[Any]]
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
    def get_subdata(cls, num: Optional[int]) -> Any:
        subdata = cls._get_data(num)[1]

        if not subdata:
            raise ValueError('Sub-data not available')

        return subdata


class UsageTypes(enum.Enum):
    # controls
    LINEAR_CONTROL = LC = 0
    ON_OFF_CONTROL = OOC = 1
    MOMENTARY_CONTROL = MC = 2
    ONE_SHOT_CONTROL = OSC = 3
    RE_TRIGGER_CONTROL = RTC = 4
    # data
    SELECTOR = SEL = 5
    STATIC_VALUE = SV = 6
    STATIC_FLAG = SF = 7
    DYNAMIC_FLAG = DF = 8
    DYNAMIC_VALUE = DV = 9
    # collection
    NAMED_ARRAY = NARY = 10
    COLLECTION_APPLICATION = CA = 11
    COLLECTION_LOGICAL = CL = 12
    COLLECTION_PHYSICAL = CP = 13
    USAGE_SWITCH = US = 14
    USAGE_MODIFIER = UM = 15


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


class KeyboardKeypad(_Data):
    NO_EVENT = 0x00, 'No event indicated', UsageTypes.SEL
    KEYBOARD_ERROR_ROLL_OVER = 0x01, 'Keyboard ErrorRollOver', UsageTypes.SEL
    KEYBOARD_POST = 0x02, 'Keyboard POSTFail', UsageTypes.SEL
    KEYBOARD_ERROR_UNDEFINED = 0x03, 'Keyboard ErrorUndefined', UsageTypes.SEL
    KEYBOARD_A = 0x04, 'Keyboard a and A', UsageTypes.SEL
    KEYBOARD_B = 0x05, 'Keyboard b and B', UsageTypes.SEL
    KEYBOARD_C = 0x06, 'Keyboard c and C', UsageTypes.SEL
    KEYBOARD_D = 0x07, 'Keyboard d and D', UsageTypes.SEL
    KEYBOARD_E = 0x08, 'Keyboard e and E', UsageTypes.SEL
    KEYBOARD_F = 0x09, 'Keyboard f and F', UsageTypes.SEL
    KEYBOARD_G = 0x0A, 'Keyboard g and G', UsageTypes.SEL
    KEYBOARD_H = 0x0B, 'Keyboard h and H', UsageTypes.SEL
    KEYBOARD_I = 0x0C, 'Keyboard i and I', UsageTypes.SEL
    KEYBOARD_J = 0x0D, 'Keyboard j and J', UsageTypes.SEL
    KEYBOARD_K = 0x0E, 'Keyboard k and K', UsageTypes.SEL
    KEYBOARD_L = 0x0F, 'Keyboard l and L', UsageTypes.SEL
    KEYBOARD_M = 0x10, 'Keyboard m and M', UsageTypes.SEL
    KEYBOARD_N = 0x11, 'Keyboard n and N', UsageTypes.SEL
    KEYBOARD_O = 0x12, 'Keyboard o and O', UsageTypes.SEL
    KEYBOARD_P = 0x13, 'Keyboard p and P', UsageTypes.SEL
    KEYBOARD_Q = 0x14, 'Keyboard q and Q', UsageTypes.SEL
    KEYBOARD_R = 0x15, 'Keyboard r and R', UsageTypes.SEL
    KEYBOARD_S = 0x16, 'Keyboard s and S', UsageTypes.SEL
    KEYBOARD_T = 0x17, 'Keyboard t and T', UsageTypes.SEL
    KEYBOARD_U = 0x18, 'Keyboard u and U', UsageTypes.SEL
    KEYBOARD_V = 0x19, 'Keyboard v and V', UsageTypes.SEL
    KEYBOARD_W = 0x1A, 'Keyboard w and W', UsageTypes.SEL
    KEYBOARD_X = 0x1B, 'Keyboard x and X', UsageTypes.SEL
    KEYBOARD_Y = 0x1C, 'Keyboard y and Y', UsageTypes.SEL
    KEYBOARD_Z = 0x1D, 'Keyboard z and Z', UsageTypes.SEL
    KEYBOARD_1 = 0x1E, 'Keyboard 1 and !', UsageTypes.SEL
    KEYBOARD_2 = 0x1F, 'Keyboard 2 and @', UsageTypes.SEL
    KEYBOARD_3 = 0x20, 'Keyboard 3 and #', UsageTypes.SEL
    KEYBOARD_4 = 0x21, 'Keyboard 4 and $', UsageTypes.SEL
    KEYBOARD_5 = 0x22, 'Keyboard 5 and %', UsageTypes.SEL
    KEYBOARD_6 = 0x23, 'Keyboard 6 and ^', UsageTypes.SEL
    KEYBOARD_7 = 0x24, 'Keyboard 7 and &', UsageTypes.SEL
    KEYBOARD_8 = 0x25, 'Keyboard 8 and *', UsageTypes.SEL
    KEYBOARD_9 = 0x26, 'Keyboard 9 and (', UsageTypes.SEL
    KEYBOARD_0 = 0x27, 'Keyboard 0 and )', UsageTypes.SEL
    KEYBOARD_ENTER = 0x28, 'Keyboard Return (ENTER)', UsageTypes.SEL
    KEYBOARD_ESCAPE = 0x29, 'Keyboard ESCAPE', UsageTypes.SEL
    KEYBOARD_DELETE = 0x2A, 'Keyboard DELETE (Backspace)', UsageTypes.SEL
    KEYBOARD_TAB = 0x2B, 'Keyboard Tab', UsageTypes.SEL
    KEYBOARD_SPACEBAR = 0x2C, 'Keyboard Spacebar', UsageTypes.SEL
    KEYBOARD_MINUS = 0x2D, 'Keyboard - and (underscore)', UsageTypes.SEL
    KEYBOARD_PLUS = 0x2E, 'Keyboard = and +', UsageTypes.SEL
    KEYBOARD_LEFT_BRACKET = 0x2F, 'Keyboard [ and {', UsageTypes.SEL
    KEYBOARD_RIGHT_BRACKET = 0x30, 'Keyboard ] and }', UsageTypes.SEL
    KEYBOARD_BACKSLASH = 0x31, 'Keyboard \\ and |', UsageTypes.SEL
    KEYBOARD_CARDINAL = 0x32, 'Keyboard Non-US # and ~', UsageTypes.SEL
    KEYBOARD_SEMICOLON = 0x33, 'Keyboard ; and :', UsageTypes.SEL
    KEYBOARD_QUOTE = 0x34, 'Keyboard \' and "', UsageTypes.SEL
    KEYBOARD_GRAVE = 0x35, 'Keyboard Grave Accent and Tilde', UsageTypes.SEL
    KEYBOARD_COMMA = 0x36, 'Keyboard , and <', UsageTypes.SEL
    KEYBOARD_DOT = 0x37, 'Keyboard . and >', UsageTypes.SEL
    KEYBOARD_SLASH = 0x38, 'Keyboard / and ?', UsageTypes.SEL
    KEYBOARD_CAPS_LOCK = 0x39, 'Keyboard Caps Lock', UsageTypes.SEL
    KEYBOARD_F1 = 0x3A, 'Keyboard F1', UsageTypes.SEL
    KEYBOARD_F2 = 0x3B, 'Keyboard F2', UsageTypes.SEL
    KEYBOARD_F3 = 0x3C, 'Keyboard F3', UsageTypes.SEL
    KEYBOARD_F4 = 0x3D, 'Keyboard F4', UsageTypes.SEL
    KEYBOARD_F5 = 0x3E, 'Keyboard F5', UsageTypes.SEL
    KEYBOARD_F6 = 0x3F, 'Keyboard F6', UsageTypes.SEL
    KEYBOARD_F7 = 0x40, 'Keyboard F7', UsageTypes.SEL
    KEYBOARD_F8 = 0x41, 'Keyboard F8', UsageTypes.SEL
    KEYBOARD_F9 = 0x42, 'Keyboard F9', UsageTypes.SEL
    KEYBOARD_F10 = 0x43, 'Keyboard F10', UsageTypes.SEL
    KEYBOARD_F11 = 0x44, 'Keyboard F11', UsageTypes.SEL
    KEYBOARD_F12 = 0x45, 'Keyboard F12', UsageTypes.SEL
    KEYBOARD_PRINTSCREEN = 0x46, 'Keyboard PrintScreen', UsageTypes.SEL
    KEYBOARD_SCROLL_LOCK = 0x47, 'Keyboard Scroll Lock', UsageTypes.SEL
    KEYBOARD_PAUSE = 0x48, 'Keyboard Pause', UsageTypes.SEL
    KEYBOARD_INSERT = 0x49, 'Keyboard Insert', UsageTypes.SEL
    KEYBOARD_HOME = 0x4A, 'Keyboard Home', UsageTypes.SEL
    KEYBOARD_PAGE_UP = 0x4B, 'Keyboard PageUp', UsageTypes.SEL
    KEYBOARD_DELETE_FORWARD = 0x4C, 'Keyboard Delete Forward', UsageTypes.SEL
    KEYBOARD_END = 0x4D, 'Keyboard End', UsageTypes.SEL
    KEYBOARD_PAGE_DOWN = 0x4E, 'Keyboard PageDown', UsageTypes.SEL
    KEYBOARD_RIGHT_ARROW = 0x4F, 'Keyboard RightArrow', UsageTypes.SEL
    KEYBOARD_LEFT_ARROW = 0x50, 'Keyboard LeftArrow', UsageTypes.SEL
    KEYBOARD_UP_ARROW = 0x51, 'Keyboard DownArrow', UsageTypes.SEL
    KEYBOARD_DOWN_ARROW = 0x52, 'Keyboard UpArrow', UsageTypes.SEL
    KEYBOARD_NUM_LOCK = 0x53, 'Keypad Num Lock and Clear', UsageTypes.SEL
    KEYPAD_SLASH = 0x54, 'Keypad /', UsageTypes.SEL
    KEYPAD_ASTERISK = 0x55, 'Keypad *', UsageTypes.SEL
    KEYPAD_MINUS = 0x56, 'Keypad -', UsageTypes.SEL
    KEYPAD_PLUS = 0x57, 'Keypad +', UsageTypes.SEL
    KEYPAD_ENTER = 0x58, 'Keypad ENTER', UsageTypes.SEL
    KEYPAD_1 = 0x59, 'Keypad 1 and End', UsageTypes.SEL
    KEYPAD_2 = 0x5A, 'Keypad 2 and Down Arrow', UsageTypes.SEL
    KEYPAD_3 = 0x5B, 'Keypad 3 and PageDn', UsageTypes.SEL
    KEYPAD_4 = 0x5C, 'Keypad 4 and Left Arrow', UsageTypes.SEL
    KEYPAD_5 = 0x5D, 'Keypad 5', UsageTypes.SEL
    KEYPAD_6 = 0x5E, 'Keypad 6 and Right Arrow', UsageTypes.SEL
    KEYPAD_7 = 0x5F, 'Keypad 7 and Home', UsageTypes.SEL
    KEYPAD_8 = 0x60, 'Keypad 8 and Up Arrow', UsageTypes.SEL
    KEYPAD_9 = 0x61, 'Keypad 9 and PageUp', UsageTypes.SEL
    KEYPAD_0 = 0x62, 'Keypad 0 and Insert', UsageTypes.SEL
    KEYPAD_DOT = 0x63, 'Keypad . and Delete', UsageTypes.SEL
    KEYPAD_BACKSLASH = 0x64, 'Keyboard Non-US \\ and |', UsageTypes.SEL
    KEYPAD_APPLICATION = 0x65, 'Keyboard Application', UsageTypes.SEL
    KEYPAD_POWER = 0x66, 'Keyboard Power', UsageTypes.SEL
    KEYPAD_EQUALS = 0x67, 'Keypad =', UsageTypes.SEL
    KEYBOARD_F13 = 0x68, 'Keyboard F13', UsageTypes.SEL
    KEYBOARD_F14 = 0x69, 'Keyboard F14', UsageTypes.SEL
    KEYBOARD_F15 = 0x6A, 'Keyboard F15', UsageTypes.SEL
    KEYBOARD_F16 = 0x6B, 'Keyboard F16', UsageTypes.SEL
    KEYBOARD_F17 = 0x6C, 'Keyboard F17', UsageTypes.SEL
    KEYBOARD_F18 = 0x6D, 'Keyboard F18', UsageTypes.SEL
    KEYBOARD_F19 = 0x6E, 'Keyboard F19', UsageTypes.SEL
    KEYBOARD_F20 = 0x6F, 'Keyboard F20', UsageTypes.SEL
    KEYBOARD_F21 = 0x70, 'Keyboard F21', UsageTypes.SEL
    KEYBOARD_F22 = 0x71, 'Keyboard F22', UsageTypes.SEL
    KEYBOARD_F23 = 0x72, 'Keyboard F23', UsageTypes.SEL
    KEYBOARD_F24 = 0x73, 'Keyboard F24', UsageTypes.SEL
    KEYBOARD_EXECUTE = 0x74, 'Keyboard Execute', UsageTypes.SEL
    KEYBOARD_HELP = 0x75, 'Keyboard Help', UsageTypes.SEL
    KEYBOARD_MENU = 0x76, 'Keyboard Menu', UsageTypes.SEL
    KEYBOARD_SELECT = 0x77, 'Keyboard Select', UsageTypes.SEL
    KEYBOARD_STOP = 0x78, 'Keyboard Stop', UsageTypes.SEL
    KEYBOARD_AGAIN = 0x79, 'Keyboard Again', UsageTypes.SEL
    KEYBOARD_UNDO = 0x7A, 'Keyboard Undo', UsageTypes.SEL
    KEYBOARD_CUT = 0x7B, 'Keyboard Cut', UsageTypes.SEL
    KEYBOARD_COPY = 0x7C, 'Keyboard Copy', UsageTypes.SEL
    KEYBOARD_PASTE = 0x7D, 'Keyboard Paste', UsageTypes.SEL
    KEYBOARD_FIND = 0x7E, 'Keyboard Find', UsageTypes.SEL
    KEYBOARD_MUTE = 0x7F, 'Keyboard Mute', UsageTypes.SEL
    KEYBOARD_VOLUME_UP = 0x80, 'Keyboard Volume Up', UsageTypes.SEL
    KEYBOARD_VOLUME_DOWN = 0x81, 'Keyboard Volume Down', UsageTypes.SEL
    KEYBOARD_LOCKING_CAPS_LOCK = 0x82, 'Keyboard Locking Caps Lock', UsageTypes.SEL
    KEYBOARD_LOCKING_NUM_LOCK = 0x83, 'Keyboard Locking Num Lock', UsageTypes.SEL
    KEYBOARD_LOCKING_SCROLL_LOCK = 0x84, 'Keyboard Locking Scroll Lock', UsageTypes.SEL
    KEYPAD_COMMA = 0x85, 'Keypad Comma', UsageTypes.SEL
    KEYPAD_EQUALS = 0x86, 'Keypad Equal Sign', UsageTypes.SEL
    KEYBOARD_INTERNATIONAL1 = 0x87, 'Keyboard International1', UsageTypes.SEL
    KEYBOARD_INTERNATIONAL2 = 0x88, 'Keyboard International2', UsageTypes.SEL
    KEYBOARD_INTERNATIONAL3 = 0x89, 'Keyboard International3', UsageTypes.SEL
    KEYBOARD_INTERNATIONAL4 = 0x8A, 'Keyboard International4', UsageTypes.SEL
    KEYBOARD_INTERNATIONAL5 = 0x8B, 'Keyboard International5', UsageTypes.SEL
    KEYBOARD_INTERNATIONAL6 = 0x8C, 'Keyboard International6', UsageTypes.SEL
    KEYBOARD_INTERNATIONAL7 = 0x8D, 'Keyboard International7', UsageTypes.SEL
    KEYBOARD_INTERNATIONAL8 = 0x8E, 'Keyboard International8', UsageTypes.SEL
    KEYBOARD_INTERNATIONAL9 = 0x8F, 'Keyboard International9', UsageTypes.SEL
    KEYBOARD_LANG1 = 0x90, 'Keyboard LANG1', UsageTypes.SEL
    KEYBOARD_LANG2 = 0x91, 'Keyboard LANG2', UsageTypes.SEL
    KEYBOARD_LANG3 = 0x92, 'Keyboard LANG3', UsageTypes.SEL
    KEYBOARD_LANG4 = 0x93, 'Keyboard LANG4', UsageTypes.SEL
    KEYBOARD_LANG5 = 0x94, 'Keyboard LANG5', UsageTypes.SEL
    KEYBOARD_LANG6 = 0x95, 'Keyboard LANG6', UsageTypes.SEL
    KEYBOARD_LANG7 = 0x96, 'Keyboard LANG7', UsageTypes.SEL
    KEYBOARD_LANG8 = 0x97, 'Keyboard LANG8', UsageTypes.SEL
    KEYBOARD_LANG9 = 0x98, 'Keyboard LANG9', UsageTypes.SEL
    KEYBOARD_ALTERNATE_ERASE = 0x99, 'Keyboard Alternate Erase', UsageTypes.SEL
    KEYBOARD_SYSREQ_ATTENTION = 0x9A, 'Keyboard SysReq/Attention', UsageTypes.SEL
    KEYBOARD_CANCEL = 0x9B, 'Keyboard Cancel', UsageTypes.SEL
    KEYBOARD_CLEAR = 0x9C, 'Keyboard Clear', UsageTypes.SEL
    KEYBOARD_PRIOR = 0x9D, 'Keyboard Prior', UsageTypes.SEL
    KEYBOARD_RETURN = 0x9E, 'Keyboard Return', UsageTypes.SEL
    KEYBOARD_SEPARATOE = 0x9F, 'Keyboard Separator', UsageTypes.SEL
    KEYBOARD_OUT = 0xA0, 'Keyboard Out', UsageTypes.SEL
    KEYBOARD_OPER = 0xA1, 'Keyboard Oper', UsageTypes.SEL
    KEYBOARD_CLEAR_AGAIN = 0xA2, 'Keyboard Clear/Again', UsageTypes.SEL
    KEYBOARD_CRSEL_PROPS = 0xA3, 'Keyboard CrSel/Props', UsageTypes.SEL
    KEYBOARD_EXSELL = 0xA4, 'Keyboard ExSel', UsageTypes.SEL
    KEYPAD_ZERO_ZERO = 0xB0, 'Keypad 00', UsageTypes.SEL
    KEYPAD_ZERO_ZERO_ZERO = 0xB1, 'Keypad 000', UsageTypes.SEL
    THOUSANDS_SEPARATOR = 0xB2, 'Thousands Separator', UsageTypes.SEL
    DECIMAL_SEPARATOR = 0xB3, 'Decimal Separator', UsageTypes.SEL
    CURRENCY_UNIT = 0xB4, 'Currency Unit', UsageTypes.SEL
    CURRENCY_SUBUNIT = 0xB5, 'Currency Sub-unit', UsageTypes.SEL
    KEYPAD_LEFT_PARENTHESIS = 0xB6, 'Keypad (', UsageTypes.SEL
    KEYPAD_RIGHT_PARENTHESIS = 0xB7, 'Keypad )', UsageTypes.SEL
    KEYPAD_LEFT_CURLY_BRACKET = 0xB8, 'Keypad {', UsageTypes.SEL
    KEYPAD_RIGHT_CURLY_BRACKET = 0xB9, 'Keypad }', UsageTypes.SEL
    KEYPAD_TAB = 0xBA, 'Keypad Tab', UsageTypes.SEL
    KEYPAD_BACKSPACE = 0xBB, 'Keypad Backspace', UsageTypes.SEL
    KEYPAD_A = 0xBC, 'Keypad A', UsageTypes.SEL
    KEYPAD_B = 0xBD, 'Keypad B', UsageTypes.SEL
    KEYPAD_C = 0xBE, 'Keypad C', UsageTypes.SEL
    KEYPAD_D = 0xBF, 'Keypad D', UsageTypes.SEL
    KEYPAD_E = 0xC0, 'Keypad E', UsageTypes.SEL
    KEYPAD_F = 0xC1, 'Keypad F', UsageTypes.SEL
    KEYPAD_XOR = 0xC2, 'Keypad XOR', UsageTypes.SEL
    KEYPAD_AND = 0xC3, 'Keypad ^', UsageTypes.SEL
    KEYPAD_PERCENTAGE = 0xC4, 'Keypad %', UsageTypes.SEL
    KEYPAD_LESS_THAN = 0xC5, 'Keypad <', UsageTypes.SEL
    KEYPAD_MORE_THAN = 0xC6, 'Keypad >', UsageTypes.SEL
    KEYPAD_AMPERSAND = 0xC7, 'Keypad &', UsageTypes.SEL
    KEYPAD_2_AMPERSAND = 0xC8, 'Keypad &&', UsageTypes.SEL
    KEYPAD_VERTICAL_BAR = 0xC9, 'Keypad |', UsageTypes.SEL
    KEYPAD_2_VERTICAL_BAR = 0xCA, 'Keypad ||', UsageTypes.SEL
    KEYPAD_COLON = 0xCB, 'Keypad :', UsageTypes.SEL
    KEYPAD_CARDINAL = 0xCC, 'Keypad #', UsageTypes.SEL
    KEYPAD_SPACE = 0xCD, 'Keypad Space', UsageTypes.SEL
    KEYPAD_AT = 0xCE, 'Keypad @', UsageTypes.SEL
    KEYPAD_EXCLAMATION = 0xCF, 'Keypad !', UsageTypes.SEL
    KEYPAD_MEMORY_STORE = 0xD0, 'Keypad Memory Store', UsageTypes.SEL
    KEYPAD_MEMORY_RECALL = 0xD1, 'Keypad Memory Recall', UsageTypes.SEL
    KEYPAD_MEMORY_CLEAR = 0xD2, 'Keypad Memory Clear', UsageTypes.SEL
    KEYPAD_MEMORY_ADD = 0xD3, 'Keypad Memory Add', UsageTypes.SEL
    KEYPAD_MEMORY_SUBTRACT = 0xD4, 'Keypad Memory Subtract', UsageTypes.SEL
    KEYPAD_MEMORY_MULTIPLY = 0xD5, 'Keypad Memory Multiply', UsageTypes.SEL
    KEYPAD_MEMORY_DIVIDE = 0xD6, 'Keypad Memory Divide', UsageTypes.SEL
    KEYPAD_PLUS_MINUS = 0xD7, 'Keypad +/-', UsageTypes.SEL
    KEYPAD_CLEAR = 0xD8, 'Keypad Clear', UsageTypes.SEL
    KEYPAD_CLEAR_ENTRY = 0xD9, 'Keypad Clear Entry', UsageTypes.SEL
    KEYPAD_BINARY = 0xDA, 'Keypad Binary', UsageTypes.SEL
    KEYPAD_OCTAL = 0xDB, 'Keypad Octal', UsageTypes.SEL
    KEYPAD_DECIMAL = 0xDC, 'Keypad Decimal', UsageTypes.SEL
    KEYPAD_HEXADECIMAL = 0xDD, 'Keypad Hexadecimal', UsageTypes.DV
    KEYBOARD_LEFT_CONTROL = 0xE0, 'Keyboard LeftControl', UsageTypes.DV
    KEYBOARD_LEFT_SHIFT = 0xE1, 'Keyboard LeftShift', UsageTypes.DV
    KEYBOARD_LEFT_ALT = 0xE2, 'Keyboard LeftAlt', UsageTypes.DV
    KEYBOARD_LEFT_GUI = 0xE3, 'Keyboard Left GUI', UsageTypes.DV
    KEYBOARD_RIGHT_CONTROL = 0xE4, 'Keyboard RightControl', UsageTypes.DV
    KEYBOARD_RIGHT_SHIFT = 0xE5, 'Keyboard RightShift', UsageTypes.DV
    KEYBOARD_RIGHT_ALT = 0xE6, 'Keyboard RightAlt', UsageTypes.DV
    KEYBOARD_RIGHT_GUI = 0xE7, 'Keyboard Right GUI', UsageTypes.DV


class Led(_Data):
    NUM_LOCK = 0x01, 'Num Lock'
    CAPS_LOCK = 0x02, 'Caps Lock'
    SCROLL_LOCK = 0x03, 'Scroll Lock'
    COMPOSE = 0x04, 'Compose'
    KANA = 0x05, 'Kana'
    POWER = 0x06, 'Power'
    SHIFT = 0x07, 'Shift'
    DO_NOT_DISTURB = 0x08, 'Do Not Disturb'
    MUTE = 0x09, 'Mute'
    TONE_ENABLE = 0x0A, 'Tone Enable'
    HIGH_CUT_FILTER = 0x0B, 'High Cut Filter'
    LOW_CUT_FILTER = 0x0C, 'Low Cut Filter'
    EQUALIZER_ENABLE = 0x0D, 'Equalizer Enable'
    SOUND_FIELD_ON = 0x0E, 'Sound Field On'
    SURROUND_ON = 0x0F, 'Surround On'
    REPEAR = 0x10, 'Repeat'
    STEREO = 0x11, 'Stereo'
    SAMPLING_RATE_DETECT = 0x12, 'Sampling Rate Detect'
    SPINNING = 0x13, 'Spinning'
    CAV = 0x14, 'CAV'
    CLV = 0x15, 'CLV'
    RECORDING_FORMAT_DETECT = 0x16, 'Recording Format Detect'
    OFF_HOOK = 0x17, 'Off-Hook'
    RING = 0x18, 'Ring'
    MESSAGE_WAITING = 0x19, 'Message Waiting'
    DATA_MODE = 0x1A, 'Data Mode'
    BATTERY_OPERATION = 0x1B, 'Battery Operation'
    BATTERY_OK = 0x1C, 'Battery OK'
    BATTERY_LOW = 0x1D, 'Battery Low'
    SPEAKER = 0x1E, 'Speaker'
    HEAD_SET = 0x1F, 'Head Set'
    HOLD = 0x20, 'Hold'
    MICROPHONE = 0x21, 'Microphone'
    COVERAGE = 0x22, 'Coverage'
    NIGHT_MODE = 0x23, 'Night Mode'
    SEND_CALLS = 0x24, 'Send Calls'
    CALL_PICKUP = 0x25, 'Call Pickup'
    CONFERENCE = 0x26, 'Conference'
    STAND_BY = 0x27, 'Stand-by'
    CAMERA_ON = 0x28, 'Camera On'
    CAMERA_OFF = 0x29, 'Camera Off'
    ON_LINE = 0x2A, 'On-Line'
    OFF_LINE = 0x2B, 'Off-Line'
    BUSY = 0x2C, 'Busy'
    READY = 0x2D, 'Ready'
    PAPER_OUT = 0x2E, 'Paper-Out'
    PAPER_JAM = 0x2F, 'Paper-Jam'
    REMOTE = 0x30, 'Remote'
    FORWARD = 0x31, 'Forward'
    REVERSE = 0x32, 'Reverse'
    STOP = 0x33, 'Stop'
    REWIND = 0x34, 'Rewind'
    FAST_FORWARD = 0x35, 'Fast Forward'
    PLAY = 0x36, 'Play'
    PAUSE = 0x37, 'Pause'
    RECORD = 0x38, 'Record'
    ERROR = 0x39, 'Error'
    USAGE_SELECTED_INDICATOR = 0x3A, 'Usage Selected Indicator'
    USAGE_IN_USE_INDICATOR = 0x3B, 'Usage In Use Indicator'
    USAGE_MULTI_MODE_INDICATOR = 0x3C, 'Usage Multi Mode Indicator'
    INDICATOR_ON = 0x3D, 'Indicator On'
    INDICATOR_FLASH = 0x3E, 'Indicator Flash'
    INDICATOR_SLOW_BLINK = 0x3F, 'Indicator Slow Blink'
    INDICATOR_FAST_BLINK = 0x40, 'Indicator Fast Blink'
    INDICATOR_OFF = 0x41, 'Indicator Off'
    FLASH_ON_TIME = 0x42, 'Flash On Time'
    SLOW_BLINK_ON_TIME = 0x43, 'Slow Blink On Time'
    SLOW_BLINK_OFF_TIME = 0x44, 'Slow Blink Off Time'
    FAST_BLINK_ON_TIME = 0x45, 'Fast Blink On Time'
    FAST_BLINK_OFF_TIME = 0x46, 'Fast Blink Off Time'
    USAGE_INDICATOR_COLOR = 0x47, 'Usage Indicator Color'
    INDICATOR_RED = 0x48, 'Indicator Red'
    INDICATOR_GREEN = 0x49, 'Indicator Green'
    INDICATOR_AMBER = 0x4A, 'Indicator Amber'
    GENERIC_INDICATOR = 0x4B, 'Generic Indicator'
    SYSTEM_SUSPEND = 0x4C, 'System Suspend'
    EXTERNAL_POWER_CONNECTED = 0x4D, 'External Power Connected'


class Button(_Data):
    data = {
        'NO_BUTTON': (0x0000, 'Button 1 (primary/trigger)'),
        'BUTTON_1': (0x0001, 'Button 1 (primary/trigger)'),
        'BUTTON_2': (0x0002, 'Button 2 (secondary)'),
        'BUTTON_3': (0x0003, 'Button 3 (tertiary)'),
    }

    for _i in range(0x0004, 0xffff):
        data[f'BUTTON_{_i}'] = _i, f'Button {_i}'


class Consumer(_Data):
    CONSUMER_CONTROL = 0x0001, 'Consumer Control'
    NUMERIC_KEY_PAD = 0x0002, 'Numeric Key Pad'
    PROGRAMMABLE_BUTTONS = 0x0003, 'Programmable Buttons'
    MICROPHONE = 0x0004, 'Microphone'
    HEADPHONE = 0x0005, 'Headphone'
    GRAPHIC_EQUALIZER = 0x0006, 'Graphic Equalizer'
    PLUS10 = 0x0020, '+10'
    PULS100 = 0x0021, '+100'
    AM_PM = 0x0022, 'AM/PM'
    POWER = 0x0030, 'Power'
    REST = 0x0031, 'Reset'
    SLEEP = 0x0032, 'Sleep'
    SLEEP_AFTER = 0x0033, 'Sleep After'
    SLEEP_MODE = 0x0034, 'Sleep Mode'
    ILLUMINATION = 0x0035, 'Illumination'
    FUNCTION_BUTTONS = 0x0036, 'Function Buttons'
    MENU = 0x0040, 'Menu'
    MENU_PICK = 0x0041, 'Menu Pick'
    MENU_UP = 0x0042, 'Menu Up'
    MENU_DOWN = 0x0043, 'Menu Down'
    MENU_LEFT = 0x0044, 'Menu Left'
    MENU_RIGHT = 0x0045, 'Menu Right'
    MENU_ESCAPE = 0x0046, 'Menu Escape'
    MENU_VALUE_INCREASE = 0x0047, 'Menu Value Increase'
    MENU_VALUE_DECREASE = 0x0048, 'Menu Value Decrease'
    DATA_ON_SCREEN = 0x0060, 'Data On Screen'
    CLOSED_CAPTION = 0x0061, 'Closed Caption'
    CLOSED_CAPTION_SELECT = 0x0062, 'Closed Caption Select'
    VCR_TV = 0x0063, 'VCR/TV'
    BROADCAST_MODE = 0x0064, 'Broadcast Mode'
    SNAPSHOT = 0x0065, 'Snapshot'
    STILL = 0x0066, 'Still'
    SELECTION = 0x0080, 'Selection'
    ASSIGN_SELECTION = 0x0081, 'Assign Selection'
    MODE_STEP = 0x0082, 'Mode Step'
    RECALL_LAST = 0x0083, 'Recall Last'
    ENTER_CHANNEL = 0x0084, 'Enter Channel'
    ORDER_MOVIE = 0x0085, 'Order Movie'
    CHANNEL = 0x0086, 'Channel'
    MEDIA_SELECTION = 0x0087, 'Media Selection'
    MEDIA_SELECT_COMPUTER = 0x0088, 'Media Select Computer'
    MEDIA_SELECT_TV = 0x0089, 'Media Select TV'
    MEDIA_SELECT_WWW = 0x008A, 'Media Select WWW'
    MEDIA_SELECT_DVD = 0x008B, 'Media Select DVD'
    MEDIA_SELECT_TELEPHONE = 0x008C, 'Media Select Telephone'
    MEDIA_SELECT_PROGRAM_GUIDE = 0x008D, 'Media Select Program Guide'
    MEDIA_SELECT_VIDEO_PHONE = 0x008E, 'Media Select Video Phone'
    MEDIA_SELECT_GAMES = 0x008F, 'Media Select Games'
    MEDIA_SELECT_MESSAGES = 0x0090, 'Media Select Messages'
    MEDIA_SELECT_CD = 0x0091, 'Media Select CD '
    MEDIA_SELECT_VCR = 0x0092, 'Media Select VCR'
    MEDIA_SELECT_TUNER = 0x0093, 'Media Select Tuner'
    QUIT = 0x0094, 'Quit'
    HELP = 0x0095, 'Help'
    MEDIA_SELECT_TAPE = 0x0096, 'Media Select Tape'
    MEDIA_SELECT_CABLE = 0x0097, 'Media Select Cable'
    MEDIA_SELECT_SATELLITE = 0x0098, 'Media Select Satellite'
    MEDIA_SELECT_SECURITY = 0x0099, 'Media Select Security'
    MEDIA_SELECT_HOME = 0x009A, 'Media Select Home'
    MEDIA_SELECT_CALL = 0x009B, 'Media Select Call'
    CHANNEL_INCREMENT = 0x009C, 'Channel Increment'
    CHANNEL_DECREMENT = 0x009D, 'Channel Decrement'
    MEDIA_SELECT_SAP = 0x009E, 'Media Select SAP'
    VCR_PLUS = 0x00A0, 'VCR Plus'
    ONCE = 0x00A1, 'Once'
    DAILY = 0x00A2, 'Daily'
    WEEKLY = 0x00A3, 'Weekly'
    MONTHLY = 0x00A4, 'Monthly'
    PLAY = 0x00B0, 'Play'
    PAUSE = 0x00B1, 'Pause'
    RECORD = 0x00B2, 'Record'
    FAST_FORWARD = 0x00B3, 'Fast Forward'
    REWIND = 0x00B4, 'Rewind'
    SCAN_NEXT_TRACK = 0x00B5, 'Scan Next Track'
    SCAN_PREVIOUS_TRACK = 0x00B6, 'Scan Previous Track'
    STOP = 0x00B7, 'Stop'
    EJECT = 0x00B8, 'Eject'
    RANDOM_PLAY = 0x00B9, 'Random Play'
    SELECT_DISC = 0x00BA, 'Select Disc'
    ENTER_DISC = 0x00BB, 'Enter Disc'
    REPEAT = 0x00BC, 'Repeat'
    TRACKING = 0x00BD, 'Tracking'
    TRACK_NORMAL = 0x00BE, 'Track Normal'
    SLOW_TRACKING = 0x00BF, 'Slow Tracking'
    FRAME_FORWARD = 0x00C0, 'Frame Forward'
    FRAME_BACK = 0x00C1, 'Frame Back'
    MARK = 0x00C2, 'Mark'
    CLEAR_MARK = 0x00C3, 'Clear Mark'
    REPEAT_FROM_MARK = 0x00C4, 'Repeat From Mark'
    RETURN_TO_MARK = 0x00C5, 'Return To Mark'
    SEARCH_MARK_FORWARD = 0x00C6, 'Search Mark Forward'
    SEARCH_MARK_BACKWARDS = 0x00C7, 'Search Mark Backwards'
    COUNTER_RESET = 0x00C8, 'Counter Reset'
    SHOW_COUNTER = 0x00C9, 'Show Counter'
    TRACKING_INCREMENT = 0x00CA, 'Tracking Increment'
    TRACKING_DECREMENT = 0x00CB, 'Tracking Decrement'
    STOP_EJECT = 0x00CC, 'Stop/Eject'
    PLAY_PAUSE = 0x00CD, 'Play/Pause'
    PLAY_SKIP = 0x00CE, 'Play/Skip'
    VOLUME = 0x00E0, 'Volume'
    BALANCE = 0x00E1, 'Balance'
    MUTE = 0x00E2, 'Mute'
    BASS = 0x00E3, 'Bass'
    TREBLE = 0x00E4, 'Treble'
    BASS_BOOST = 0x00E5, 'Bass Boost'
    SURROUND_MODE = 0x00E6, 'Surround Mode'
    LOUDNESS = 0x00E7, 'Loudness'
    MPX = 0x00E8, 'MPX'
    VOLUME_INCREMENT = 0x00E9, 'Volume Increment'
    VOLUME_DECREMENT = 0x00EA, 'Volume Decrement'
    SPEED_SELECT = 0x00F0, 'Speed Select'
    PLAYBACK_SPEED = 0x00F1, 'Playback Speed'
    STANDARD_PLAY = 0x00F2, 'Standard Play'
    LONG_PLAY = 0x00F3, 'Long Play'
    EXTENDED_PLAY = 0x00F4, 'Extended Play'
    SLOW = 0x00F5, 'Slow'
    FAN_ENABLE = 0x0100, 'Fan Enable'
    FAN_SPEED = 0x0101, 'Fan Speed'
    LIGHT_ENABLE = 0x0102, 'Light Enable'
    LIGHT_ILLUMINATION_LEVEL = 0x0103, 'Light Illumination Level'
    CLIMATE_CONTROL_ENABLE = 0x0104, 'Climate Control Enable'
    ROOM_TEMPERATURE = 0x0105, 'Room Temperature'
    SECURITY_ENABLE = 0x0106, 'Security Enable'
    FIRE_ALARM = 0x0107, 'Fire Alarm'
    POLICE_ALARM = 0x0108, 'Police Alarm'
    PROXIMITY = 0x0109, 'Proximity'
    MOTION = 0x010A, 'Motion'
    DURESS_ALARM = 0x010B, 'Duress Alarm'
    HOLDUP_ALARM = 0x010C, 'Holdup Alarm'
    MEDICAL_ALARM = 0x010D, 'Medical Alarm'
    BALANCE_RIGHT = 0x0150, 'Balance Right'
    BALANCE_LEFT = 0x0151, 'Balance Left'
    BASS_INCREMENT = 0x0152, 'Bass Increment'
    BASS_DECREMENT = 0x0153, 'Bass Decrement'
    TREBLE_INCREMENT = 0x0154, 'Treble Increment'
    TREBLE_DECREMENT = 0x0155, 'Treble Decrement'
    SPEAKER_SYSTEM = 0x0160, 'Speaker System'
    CHANNEL_LEFT = 0x0161, 'Channel Left'
    CHANNEL_RIGHT = 0x0162, 'Channel Right'
    CHANNEL_CENTER = 0x0163, 'Channel Center'
    CHANNEL_FRONT = 0x0164, 'Channel Front'
    CHANNEL_CENTER_FRONT = 0x0165, 'Channel Center Front'
    CHANNEL_SIDE = 0x0166, 'Channel Side'
    CHANNEL_SURROUND = 0x0167, 'Channel Surround'
    CHANNEL_LOW_FREQUENCY_ENHANCEMENT = 0x0168, 'Channel Low Frequency Enhancement'
    CHANNEL_TOP = 0x0169, 'Channel Top'
    CHANNEL_UNKNOWN = 0x016A, 'Channel Unknown'
    SUBCHANNEL = 0x0170, 'Sub-channel'
    SUBCHANNEL_INCREMENT = 0x0171, 'Sub-channel Increment'
    SUBCHANNEL_DECREMENT = 0x0172, 'Sub-channel Decrement'
    ALTERNATE_AUDIO_INCREMENT = 0x0173, 'Alternate Audio Increment'
    ALTERNATE_AUDIO_DECREMENT = 0x0174, 'Alternate Audio Decrement'
    APPLICATION_LAUNCH_BUTTONS = 0x0180, 'Application Launch Buttons'
    AL_LAUCH_BUTTON_CONFIGURATION_TOOL = 0x0181, 'AL Launch Button Configuration Tool'
    AL_PROGRAMMABLE_BUTTON_CONFIGURATION = 0x0182, 'AL Programmable Button Configuration'
    AL_CONSUMER_CONTROL_CONFIGURATION = 0x0183, 'AL Consumer Control Configuration'
    AL_WORD_PROCESSOR = 0x0184, 'AL Word Processor'
    AL_TEXT_EDITOR = 0x0185, 'AL Text Editor'
    AL_SPREADSHEET = 0x0186, 'AL Spreadsheet'
    AL_GRAPHICS_EDITOR = 0x0187, 'AL Graphics Editor'
    AL_PRESENTATION_APP = 0x0188, 'AL Presentation App'
    AL_DATABASE_APP = 0x0189, 'AL Database App'
    AL_EMAIL_READER = 0x018A, 'AL Email Reader'
    AL_NEWSREADER = 0x018B, 'AL Newsreader'
    AL_VOICEMAIL = 0x018C, 'AL Voicemail'
    AL_CONTACTS_ADDRESS_BOOK = 0x018D, 'AL Contacts/Address Book'
    AL_CALENDAR_SCHEDULE = 0x018E, 'AL Calendar/Schedule'
    AL_TASK_PROJECT_MANAGER = 0x018F, 'AL Task/Project Manager'
    AL_LOG_JOURNAL_TIMECARD = 0x0190, 'AL Log/Journal/Timecard'
    AL_CHECKBOOK_FINANCE = 0x0191, 'AL Checkbook/Finance'
    AL_CALCULATOR = 0x0192, 'AL Calculator'
    AL_AV_CAPTURE_PLAYBACK = 0x0193, 'AL A/V Capture/Playback'
    AL_LOCAL_MACHINE_BROWSER = 0x0194, 'AL Local Machine Browser'
    AL_LAN_WAN_BROWSER = 0x0195, 'AL LAN/WAN Browser'
    AL_INTERNET_BROWSER = 0x0196, 'AL Internet Browser'
    AL_REMOTE_NETWORKING_ISP_CONNECT = 0x0197, 'AL Remote Networking/ISP Connect'
    AL_NETWORK_CONFERENCE = 0x0198, 'AL Network Conference'
    AL_NETWORK_CHAT = 0x0199, 'AL Network Chat'
    AL_TELEPHONY_DIALER = 0x019A, 'AL Telephony/Dialer'
    AL_LOGON = 0x019B, 'AL Logon'
    AL_LOGOFF = 0x019C, 'AL Logoff'
    AL_LOGON_LOGOFF = 0x019D, 'AL Logon/Logoff'
    AL_LOCK_SCREEN_SAVER = 0x019E, 'AL Terminal Lock/Screensaver'
    AL_CONTROL_PANEL = 0x019F, 'AL Control Panel'
    AL_COMMAND_LINE_PROCESSOR_RUN = 0x01A0, 'AL Command Line Processor/Run'
    AL_PROCESS_TASK_MANAGER = 0x01A1, 'AL Process/Task Manager'
    AL_SELECT_TASK_APPLICATION = 0x01A2, 'AL Select Task/Application'
    AL_NEXT_TASK_APPLICATION = 0x01A3, 'AL Next Task/Application'
    AL_PREVIOUS_TASK_APPLICATION = 0x01A4, 'AL Previous Task/Application'
    AL_HALT_TASK_APPLICATION = 0x01A5, 'AL Preemptive Halt Task/Application'
    AL_INTEGRATED_HELP_CENTER = 0x01A6, 'AL Integrated Help Center'
    AL_DOCUMENTS = 0x01A7, 'AL Documents'
    AL_THESAURUS = 0x01A8, 'AL Thesaurus'
    AL_DICTIONARY = 0x01A9, 'AL Dictionary'
    AL_DESKTOP = 0x01AA, 'AL Desktop'
    AL_SPELL_CHECK = 0x01AB, 'AL Spell Check'
    AL_GRAMMAR_CHECK = 0x01AC, 'AL Grammar Check'
    AL_WIRELESS_STATUS = 0x01AD, 'AL Wireless Status'
    AL_KEYBOARD_LAYOUT = 0x01AE, 'AL Keyboard Layout'
    AL_VIRUS_PROTECTION = 0x01AF, 'AL Virus Protection'
    AL_ENCRYPTION = 0x01B0, 'AL Encryption'
    AL_SCREEN_SAVER = 0x01B1, 'AL Screen Saver'
    AL_ALARMS = 0x01B2, 'AL Alarms'
    AL_CLOCK = 0x01B3, 'AL Clock'
    AL_FILE_BROWSER = 0x01B4, 'AL File Browser'
    AL_POWER_STATUS = 0x01B5, 'AL Power Status'
    AL_IMAGE_BROWSER = 0x01B6, 'AL Image Browser'
    AL_AUDIO_BROWSER = 0x01B7, 'AL Audio Browser'
    AL_VIDEO_BROWSER = 0x01B8, 'AL Movie Browser'
    AL_DIGITAL_RIGHTS_MANAGER = 0x01B9, 'AL Digital Rights Manager'
    AL_DIGITAL_WALLET = 0x01BA, 'AL Digital Wallet'
    AL_INSTANT_MESSAGING = 0x01BC, 'AL Instant Messaging'
    AL_OEM_FEATURES_TIPS_TUTORIAL_BROWSER = 0x01BD, 'AL OEM Features/ Tips/Tutorial Browser'
    AL_OEM_HELP = 0x01BE, 'AL OEM Help'
    AL_ONLINE_COMMUNITY = 0x01BF, 'AL Online Community'
    AL_ENTERTAINMENT_CONTENT_BROWSER = 0x01C0, 'AL Entertainment Content Browser'
    AL_ONLINE_SHOPPING_BROWSER = 0x01C1, 'AL Online Shopping Browser'
    AL_SMARTCARD_INFORMATION_HELP = 0x01C2, 'AL SmartCard Information/Help'
    AL_MARKET_MONITOR_FINANCE_BROWSER = 0x01C3, 'AL Market Monitor/Finance Browser'
    AL_CUSTOMIZED_CORPORATE_NEWS_BROWSER = 0x01C4, 'AL Customized Corporate News Browser'
    AL_ONLINE_ACTIVITY_BROWSER = 0x01C5, 'AL Online Activity Browser'
    AL_RESEARCH_SEARCH_BROWSER = 0x01C6, 'AL Research/Search Browser'
    AL_AUDIO_PLAYER = 0x01C7, 'AL Audio Player'
    GENERIC_GUI_APPLICATION_CONTROLS = 0x0200, 'Generic GUI Application Controls'
    AC_NEW = 0x0201, 'AC New'
    AC_OPEN = 0x0202, 'AC Open'
    AC_CLOSE = 0x0203, 'AC Close'
    AC_EXIT = 0x0204, 'AC Exit'
    AC_MAXIMIZE = 0x0205, 'AC Maximize'
    AC_MINIMIZE = 0x0206, 'AC Minimize'
    AC_SAVE = 0x0207, 'AC Save'
    AC_PRINT = 0x0208, 'AC Print'
    AC_PROPERTIES = 0x0209, 'AC Properties'
    AC_UNDO = 0x021A, 'AC Undo'
    AC_COPY = 0x021B, 'AC Copy'
    AC_CUT = 0x021C, 'AC Cut'
    AC_PASTE = 0x021D, 'AC Paste'
    AC_SELECT_ALL = 0x021E, 'AC Select All'
    AC_FIND = 0x021F, 'AC Find'
    AC_FIND_AND_REPLACE = 0x0220, 'AC Find and Replace'
    AC_SEARCH = 0x0221, 'AC Search'
    AC_GO_TO = 0x0222, 'AC Go To'
    AC_HOME = 0x0223, 'AC Home'
    AC_BACK = 0x0224, 'AC Back'
    AC_FORWARD = 0x0225, 'AC Forward'
    AC_STOP = 0x0226, 'AC Stop'
    AC_REFRESH = 0x0227, 'AC Refresh'
    AC_PREVIOUS_LINK = 0x0228, 'AC Previous Link'
    AC_NEXT_LINK = 0x0229, 'AC Next Link'
    AC_BOOKMARKS = 0x022A, 'AC Bookmarks'
    AC_HISTORY = 0x022B, 'AC History'
    AC_SUBSCRIPTIONS = 0x022C, 'AC Subscriptions'
    AC_ZOOM_IN = 0x022D, 'AC Zoom In'
    AC_ZOOM_OUT = 0x022E, 'AC Zoom Out'
    AC_ZOOM = 0x022F, 'AC Zoom'
    AC_FULL_SCREEN_VIEW = 0x0230, 'AC Full Screen View'
    AC_NORMAL_VIEW = 0x0231, 'AC Normal View'
    AC_VIEW_TOGGLE = 0x0232, 'AC View Toggle'
    AC_SCROLL_UP = 0x0233, 'AC Scroll Up'
    AC_SCROLL_DOWN = 0x0234, 'AC Scroll Down'
    AC_SCROLL = 0x0235, 'AC Scroll'
    AC_PAN_LEFT = 0x0236, 'AC Pan Left'
    AC_PAN_RIGHT = 0x0237, 'AC Pan Right'
    AC_PAN = 0x0238, 'AC Pan'
    AC_NEW_WINDOWS = 0x0239, 'AC New Window'
    AC_TILE_HORIZONTALLY = 0x023A, 'AC Tile Horizontally'
    AC_TILE_VERTICALLY = 0x023B, 'AC Tile Vertically'
    AC_FORMAT = 0x023C, 'AC Format'
    AC_EDIT = 0x023D, 'AC Edit'
    AC_BOLD = 0x023E, 'AC Bold'
    AC_ITALICS = 0x023F, 'AC Italics'
    AC_UNDERLINE = 0x0240, 'AC Underline'
    AC_STRIKETHROUGH = 0x0241, 'AC Strikethrough'
    AC_SUBSCRIPT = 0x0242, 'AC Subscript'
    AC_SUPERSCRIPT = 0x0243, 'AC Superscript'
    AC_ALL_CAPS = 0x0244, 'AC All Caps'
    AC_ROTATE = 0x0245, 'AC Rotate'
    AC_RESIZE = 0x0246, 'AC Resize'
    AC_FLIP_HORIZONTAL = 0x0247, 'AC Flip horizontal'
    AC_FLIP_VERTICAL = 0x0248, 'AC Flip Vertical'
    AC_MIRROR_HORIZONTAL = 0x0249, 'AC Mirror Horizontal'
    AC_MIRROR_VERTICAL = 0x024A, 'AC Mirror Vertical'
    AC_FONT_SELECT = 0x024B, 'AC Font Select'
    AC_FONT_COLOR = 0x024C, 'AC Font Color'
    AC_FONT_SIZE = 0x024D, 'AC Font Size'
    AC_JUSTIFY_LEFT = 0x024E, 'AC Justify Left'
    AC_JUSTIFY_CENTER_H = 0x024F, 'AC Justify Center H'
    AC_JUSTIFY_RIGHT = 0x0250, 'AC Justify Right'
    AC_JUSTIFY_BLOCK_H = 0x0251, 'AC Justify Block H'
    AC_JUSTIFY_TOP = 0x0252, 'AC Justify Top'
    AC_JUSTIFY_CENTER_V = 0x0253, 'AC Justify Center V'
    AC_JUSTIFY_BOTTOM = 0x0254, 'AC Justify Bottom'
    AC_JUSTIFY_BLOCK_V = 0x0255, 'AC Justify Block V'
    AC_INDENT_INCREASE = 0x0256, 'AC Indent Decrease'
    AC_INDENT_DECREASE = 0x0257, 'AC Indent Increase'
    AC_NUMBERED_LIST = 0x0258, 'AC Numbered List'
    AC_RESTART_NUMBERING = 0x0259, 'AC Restart Numbering'
    AC_BULLETED_LIST = 0x025A, 'AC Bulleted List'
    AC_PROMOTE = 0x025B, 'AC Promote'
    AC_DEMOTE = 0x025C, 'AC Demote'
    AC_YES = 0x025D, 'AC Yes'
    AC_NO = 0x025E, 'AC No'
    AC_CANCEL = 0x025F, 'AC Cancel'
    AC_CATALOG = 0x0260, 'AC Catalog'
    AC_BUY_CHECKOUT = 0x0261, 'AC Buy/Checkout'
    AC_ADD_TO_CART = 0x0262, 'AC Add to Cart'
    AC_EXPAND = 0x0263, 'AC Expand'
    AC_EXPAND_ALL = 0x0264, 'AC Expand All'
    AC_COLLAPSE = 0x0265, 'AC Collapse'
    AC_COLLAPSE_ALL = 0x0266, 'AC Collapse All'
    AC_PRINT_PREVIEW = 0x0267, 'AC Print Preview'
    AC_PASTE_SPECIAL = 0x0268, 'AC Paste Special'
    AC_INSER_MODE = 0x0269, 'AC Insert Mode'
    AC_DELETE = 0x026A, 'AC Delete'
    AC_LOCK = 0x026B, 'AC Lock'
    AC_UNLOCK = 0x026C, 'AC Unlock'
    AC_PROTECT = 0x026D, 'AC Protect'
    AC_UNPROTECT = 0x026E, 'AC Unprotect'
    AC_ATTACH_COMMENT = 0x026F, 'AC Attach Comment'
    AC_DELETE_COMMENT = 0x0270, 'AC Delete Comment'
    AC_VIEW_COMMENT = 0x0271, 'AC View Comment'
    AC_SELECT_WORD = 0x0272, 'AC Select Word'
    AC_SELECT_SENTENCE = 0x0273, 'AC Select Sentence'
    AC_SELECT_PARAGRAPH = 0x0274, 'AC Select Paragraph'
    AC_SELECT_COLUMN = 0x0275, 'AC Select Column'
    AC_SELECT_ROW = 0x0276, 'AC Select Row'
    AC_SELECT_TABLE = 0x0277, 'AC Select Table'
    AC_SELECT_OBJECT = 0x0278, 'AC Select Object'
    AC_REDO_REPEAT = 0x0279, 'AC Redo/Repeat'
    AC_SORT = 0x027A, 'AC Sort'
    AC_SORT_ASCENDING = 0x027B, 'AC Sort Ascending'
    AC_SORT_DESCENDING = 0x027C, 'AC Sort Descending'
    AC_FILTER = 0x027D, 'AC Filter'
    AC_SET_CLOCK = 0x027E, 'AC Set Clock'
    AC_VIEW_CLOCK = 0x027F, 'AC View Clock'
    AC_SELECT_TIME_ZONE = 0x0280, 'AC Select Time Zone'
    AC_EDIT_TIME_ZONES = 0x0281, 'AC Edit Time Zones'
    AC_SET_ALARM = 0x0282, 'AC Set Alarm'
    AC_CLEAR_ALARM = 0x0283, 'AC Clear Alarm'
    AC_SNOOZE_ALARM = 0x0284, 'AC Snooze Alarm'
    AC_RESET_ALARM = 0x0285, 'AC Reset Alarm'
    AC_SYNCHRONIZE = 0x0286, 'AC Synchronize'
    AC_SEND_RECEIVE = 0x0287, 'AC Send/Receive'
    AC_SEND_TO = 0x0288, 'AC Send To'
    AC_REPLY = 0x0289, 'AC Reply'
    AC_REPLY_ALL = 0x028A, 'AC Reply All'
    AC_FORWARD_MSG = 0x028B, 'AC Forward Msg'
    AC_SEND = 0x028C, 'AC Send'
    AC_ATTACH_FILE = 0x028D, 'AC Attach File'
    AC_UPLOAD = 0x028E, 'AC Upload'
    AC_DOWNLOAD = 0x028F, 'AC Download (Save Target As)'
    AC_SET_BORDERS = 0x0290, 'AC Set Borders'
    AC_INSERT_ROW = 0x0291, 'AC Insert Row'
    AC_INSERT_COLUMN = 0x0292, 'AC Insert Column'
    AC_INSERT_FILE = 0x0293, 'AC Insert File'
    AC_INSERT_PICTURE = 0x0294, 'AC Insert Picture'
    AC_INSERT_OBJECT = 0x0295, 'AC Insert Object'
    AC_INSERT_SYMBOL = 0x0296, 'AC Insert Symbol'
    AC_SAVE_AND_CLOSE = 0x0297, 'AC Save and Close'
    AC_RENAME = 0x0298, 'AC Rename'
    AC_MERGE = 0x0299, 'AC Merge'
    AC_SPLIT = 0x029A, 'AC Split'
    AC_DISTRIBUTE_HORIZONTICALLY = 0x029B, 'AC Disribute Horizontally'
    AC_DISTRIBUTE_VERTICALLY = 0x029C, 'AC Distribute Vertically'


class FIDO(_Data):
    U2F_AUTHENTICATOR_DEVICEM = 0x01, 'U2F Authenticator Device'
    INPUT_REPORT_DATA = 0x20, 'Input Report Data'
    OUTPUT_REPORT_DATA = 0x21, 'Output Report Data'


class UsagePages(_Data):
    GENERIC_DESKTOP_CONTROLS_PAGE = 0x01, 'Generic Desktop Controls', GenericDesktopControls
    SIMULATION_CONTROLS_PAGE = 0x02, 'Simulation Controls'
    VR_CONTROLS_PAGE = 0x03, 'VR Controls'
    SPORT_CONTROLS_PAGE = 0x04, 'Sport Controls'
    GAME_CONTROLS_PAGE = 0x05, 'Game Controls'
    GENERIC_DEVICE_CONTROLS_PAGE = 0x06, 'Generic Device Controls'
    KEYBOARD_KEYPAD_PAGE = 0x07, 'Keyboard/Keypad', KeyboardKeypad
    LED_PAGE = 0x08, 'LED', Led
    BUTTON_PAGE = 0x09, 'Button', Button
    ORDINAL_PAGE = 0x0A, 'Ordinal'
    TELEPHONY_PAGE = 0x0B, 'Telephony'
    CONSUMER_PAGE = 0x0C, 'Consumer', Consumer
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
    FIDO_ALLIANCE_PAGE = 0xF1D0, 'FIDO Alliance', FIDO
    VENDOR_PAGE = 0xFF00, ..., 0xFFFF, 'Vendor Page'
