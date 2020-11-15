# python-hid-parser

![checks](https://github.com/FFY00/python-hid-parser/workflows/checks/badge.svg)
![tests](https://github.com/FFY00/python-hid-parser/workflows/tests/badge.svg)
[![codecov](https://codecov.io/gh/FFY00/python-hid-parser/branch/master/graph/badge.svg?token=77hhbLAkCE)](undefined)
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
    offset=0bits, size=1byte,
    usages=[
        Usage(page=Vendor Page, usage=0x0001),
    ],
)
ArrayItem(
    offset=1byte, size=1byte,
    usages=[
        Usage(page=Vendor Page, usage=0x0001),
    ],
)
ArrayItem(
    offset=2bytes, size=1byte,
    usages=[
        Usage(page=Vendor Page, usage=0x0001),
    ],
)
ArrayItem(
    offset=3bytes, size=1byte,
    usages=[
        Usage(page=Vendor Page, usage=0x0001),
    ],
)
ArrayItem(
    offset=4bytes, size=1byte,
    usages=[
        Usage(page=Vendor Page, usage=0x0001),
    ],
)
ArrayItem(
    offset=5bytes, size=1byte,
    usages=[
        Usage(page=Vendor Page, usage=0x0001),
    ],
)
```
