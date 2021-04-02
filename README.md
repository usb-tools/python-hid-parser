# python-hid-parser

[![checks](https://github.com/usb-tools/python-hid-parser/actions/workflows/checks.yml/badge.svg)](https://github.com/usb-tools/python-hid-parser/actions/workflows/checks.yml)
[![tests](https://github.com/usb-tools/python-hid-parser/actions/workflows/tests.yml/badge.svg)](https://github.com/usb-tools/python-hid-parser/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/usb-tools/python-hid-parser/branch/main/graph/badge.svg?token=sntW7bZ1ww)](https://codecov.io/gh/usb-tools/python-hid-parser)
[![PyPI version](https://badge.fury.io/py/hid-parser.svg)](https://pypi.org/project/hid-parser/)

Typed pure Python library to parse HID report descriptors


#### Example

```python
>>> import hid_parser
>>> simple_mouse_rdesc_raw = [
...     0x05, 0x01,  # .Usage Page (Generic Desktop)        0
...     0x09, 0x02,  # .Usage (Mouse)                       2
...     0xa1, 0x01,  # .Collection (Application)            4
...     0x09, 0x02,  # ..Usage (Mouse)                      6
...     0xa1, 0x02,  # ..Collection (Logical)               8
...     0x09, 0x01,  # ...Usage (Pointer)                   10
...     0xa1, 0x00,  # ...Collection (Physical)             12
...     0x05, 0x09,  # ....Usage Page (Button)              14
...     0x19, 0x01,  # ....Usage Minimum (1)                16
...     0x29, 0x03,  # ....Usage Maximum (3)                18
...     0x15, 0x00,  # ....Logical Minimum (0)              20
...     0x25, 0x01,  # ....Logical Maximum (1)              22
...     0x75, 0x01,  # ....Report Size (1)                  24
...     0x95, 0x03,  # ....Report Count (3)                 26
...     0x81, 0x02,  # ....Input (Data,Var,Abs)             28
...     0x75, 0x05,  # ....Report Size (5)                  30
...     0x95, 0x01,  # ....Report Count (1)                 32
...     0x81, 0x03,  # ....Input (Cnst,Var,Abs)             34
...     0x05, 0x01,  # ....Usage Page (Generic Desktop)     36
...     0x09, 0x30,  # ....Usage (X)                        38
...     0x09, 0x31,  # ....Usage (Y)                        40
...     0x15, 0x81,  # ....Logical Minimum (-127)           42
...     0x25, 0x7f,  # ....Logical Maximum (127)            44
...     0x75, 0x08,  # ....Report Size (8)                  46
...     0x95, 0x02,  # ....Report Count (2)                 48
...     0x81, 0x06,  # ....Input (Data,Var,Rel)             50
...     0xc0,        # ...End Collection                    52
...     0xc0,        # ..End Collection                     53
...     0xc0,        # .End Collection                      54
... ]
>>> rdesc = hid_parser.ReportDescriptor(simple_mouse_rdesc_raw)
>>> rdesc.get_input_report_size()
3bytes
>>> for item in rdesc.get_input_items():
...     print(item)
...
VariableItem(offset=0bits, size=1bit, usage=Usage(page=Button, usage=Button 1 (primary/trigger)))
VariableItem(offset=1bit, size=1bit, usage=Usage(page=Button, usage=Button 2 (secondary)))
VariableItem(offset=2bits, size=1bit, usage=Usage(page=Button, usage=Button 3 (tertiary)))
PaddingItem(offset=3bits, size=5bits)
VariableItem(offset=1byte, size=1byte, usage=Usage(page=Generic Desktop Controls, usage=X))
VariableItem(offset=2bytes, size=1byte, usage=Usage(page=Generic Desktop Controls, usage=Y))
>>> for usage, value in rdesc.parse_input_report([0b10100000, 0x50, 0x60]):
...     print(f'{usage} = {value}')
...
Usage(page=Button, usage=Button 2 (secondary)) = False
Usage(page=Button, usage=Button 3 (tertiary)) = True
Usage(page=Button, usage=Button 1 (primary/trigger)) = True
Usage(page=Generic Desktop Controls, usage=X) = 80
Usage(page=Generic Desktop Controls, usage=Y) = 96
```

```python
>>> import hid_parser
>>> keyboard_rdesc_raw = [
...     0x05, 0x01,        # Usage Page (Generic Desktop)        0
...     0x09, 0x06,        # Usage (Keyboard)                    2
...     0xa1, 0x01,        # Collection (Application)            4
...     0x05, 0x07,        #  Usage Page (Keyboard)              6
...     0x19, 0xe0,        #  Usage Minimum (224)                8
...     0x29, 0xe7,        #  Usage Maximum (231)                10
...     0x15, 0x00,        #  Logical Minimum (0)                12
...     0x25, 0x01,        #  Logical Maximum (1)                14
...     0x75, 0x01,        #  Report Size (1)                    16
...     0x95, 0x08,        #  Report Count (8)                   18
...     0x81, 0x02,        #  Input (Data,Var,Abs)               20
...     0x95, 0x01,        #  Report Count (1)                   22
...     0x75, 0x08,        #  Report Size (8)                    24
...     0x81, 0x01,        #  Input (Cnst,Arr,Abs)               26
...     0x95, 0x03,        #  Report Count (3)                   28
...     0x75, 0x01,        #  Report Size (1)                    30
...     0x05, 0x08,        #  Usage Page (LEDs)                  32
...     0x19, 0x01,        #  Usage Minimum (1)                  34
...     0x29, 0x03,        #  Usage Maximum (3)                  36
...     0x91, 0x02,        #  Output (Data,Var,Abs)              38
...     0x95, 0x05,        #  Report Count (5)                   40
...     0x75, 0x01,        #  Report Size (1)                    42
...     0x91, 0x01,        #  Output (Cnst,Arr,Abs)              44
...     0x95, 0x06,        #  Report Count (6)                   46
...     0x75, 0x08,        #  Report Size (8)                    48
...     0x15, 0x00,        #  Logical Minimum (0)                50
...     0x26, 0xff, 0x00,  #  Logical Maximum (255)              52
...     0x05, 0x07,        #  Usage Page (Keyboard)              55
...     0x19, 0x00,        #  Usage Minimum (0)                  57
...     0x2a, 0xff, 0x00,  #  Usage Maximum (255)                59
...     0x81, 0x00,        #  Input (Data,Arr,Abs)               62
...     0xc0,              # End Collection                      64
... ]
>>> rdesc = hid_parser.ReportDescriptor(keyboard_rdesc_raw)
>>> for item in rdesc.get_input_items():
...     print(item)
...
VariableItem(offset=0bits, size=1bit, usage=Usage(page=Keyboard/Keypad, usage=Keyboard LeftControl))
VariableItem(offset=1bit, size=1bit, usage=Usage(page=Keyboard/Keypad, usage=Keyboard LeftShift))
VariableItem(offset=2bits, size=1bit, usage=Usage(page=Keyboard/Keypad, usage=Keyboard LeftAlt))
VariableItem(offset=3bits, size=1bit, usage=Usage(page=Keyboard/Keypad, usage=Keyboard Left GUI))
VariableItem(offset=4bits, size=1bit, usage=Usage(page=Keyboard/Keypad, usage=Keyboard RightControl))
VariableItem(offset=5bits, size=1bit, usage=Usage(page=Keyboard/Keypad, usage=Keyboard RightShift))
VariableItem(offset=6bits, size=1bit, usage=Usage(page=Keyboard/Keypad, usage=Keyboard RightAlt))
VariableItem(offset=7bits, size=1bit, usage=Usage(page=Keyboard/Keypad, usage=Keyboard Right GUI))
PaddingItem(offset=1byte, size=1byte)
ArrayItem(
    offset=2bytes, size=1byte, count=6,
    usages=[
        Usage(page=Keyboard/Keypad, usage=No event indicated),
        ...
        Usage(page=Keyboard/Keypad, usage=0x00ff),
    ],
)
>>> for usage, value in rdesc.parse_input_report([0b10100101, 0x00, 0x04, 0x05, 0x06, 0x00, 0x00, 0x00]):
...     print(f'{usage} = {value}')
...
Usage(page=Keyboard/Keypad, usage=Keyboard Left GUI) = 0
Usage(page=Keyboard/Keypad, usage=Keyboard LeftAlt) = 1
Usage(page=Keyboard/Keypad, usage=Keyboard RightControl) = 0
Usage(page=Keyboard/Keypad, usage=Keyboard RightShift) = 1
Usage(page=Keyboard/Keypad, usage=Keyboard RightAlt) = 0
Usage(page=Keyboard/Keypad, usage=Keyboard Right GUI) = 1
Usage(page=Keyboard/Keypad, usage=Keyboard a and A) = True
Usage(page=Keyboard/Keypad, usage=Keyboard b and B) = True
Usage(page=Keyboard/Keypad, usage=Keyboard c and C) = True
Usage(page=Keyboard/Keypad, usage=Keyboard LeftShift) = 0
Usage(page=Keyboard/Keypad, usage=Keyboard LeftControl) = 1
```

```python
>>> import hid_parser
>>> vendor_command_rdesc_raw = [
...     0x06, 0x00, 0xff,  # .Usage Page (Vendor Defined Page 1)  0
...     0x09, 0x01,        # .Usage (Vendor Usage 1)              3
...     0xa1, 0x01,        # .Collection (Application)            5
...     0x85, 0x10,        # ..Report ID (16)                     7
...     0x75, 0x08,        # ..Report Size (8)                    9
...     0x95, 0x06,        # ..Report Count (6)                   11
...     0x15, 0x00,        # ..Logical Minimum (0)                12
...     0x26, 0xff, 0x00,  # ..Logical Maximum (255)              15
...     0x09, 0x01,        # ..Usage (Vendor Usage 1)             18
...     0x81, 0x00,        # ..Input (Data,Arr,Abs)               20
...     0x09, 0x01,        # ..Usage (Vendor Usage 1)             22
...     0x91, 0x00,        # ..Output (Data,Arr,Abs)              24
...     0xc0,              # .End Collection                      26
... ]
>>> rdesc = hid_parser.ReportDescriptor(vendor_command_rdesc_raw)
>>> rdesc.get_input_report_size(0x10)
6bytes
>>> for item in rdesc.get_input_items(0x10):
...     print(item)
...
ArrayItem(
    offset=0bits, size=1byte, count=6,
    usages=[
        Usage(page=Vendor Page, usage=0x0001),
    ],
)
>>> for usage, value in rdesc.parse_input_report([0x10, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08]))
...     print(f'{usage} = {value}')
...
Usage(page=Vendor Page, usage=0x0001) = 257
Usage(page=Vendor Page, usage=0x0002) = 514
Usage(page=Vendor Page, usage=0x0003) = 771
Usage(page=Vendor Page, usage=0x0004) = 1028
Usage(page=Vendor Page, usage=0x0005) = 1285
Usage(page=Vendor Page, usage=0x0006) = 1542
```
