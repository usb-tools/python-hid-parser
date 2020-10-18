# SPDX-License-Identifier: MIT

import io
import os.path

import pytest

import hid_parser


simple_mouse_rdesc = [
    0x05, 0x01,  # .Usage Page (Generic Desktop)        0
    0x09, 0x02,  # .Usage (Mouse)                       2
    0xa1, 0x01,  # .Collection (Application)            4
    0x09, 0x02,  # ..Usage (Mouse)                      6
    0xa1, 0x02,  # ..Collection (Logical)               8
    0x09, 0x01,  # ...Usage (Pointer)                   10
    0xa1, 0x00,  # ...Collection (Physical)             12
    0x05, 0x09,  # ....Usage Page (Button)              14
    0x19, 0x01,  # ....Usage Minimum (1)                16
    0x29, 0x03,  # ....Usage Maximum (3)                18
    0x15, 0x00,  # ....Logical Minimum (0)              20
    0x25, 0x01,  # ....Logical Maximum (1)              22
    0x75, 0x01,  # ....Report Size (1)                  24
    0x95, 0x03,  # ....Report Count (3)                 26
    0x81, 0x02,  # ....Input (Data,Var,Abs)             28
    0x75, 0x05,  # ....Report Size (5)                  30
    0x95, 0x01,  # ....Report Count (1)                 32
    0x81, 0x03,  # ....Input (Cnst,Var,Abs)             34
    0x05, 0x01,  # ....Usage Page (Generic Desktop)     36
    0x09, 0x30,  # ....Usage (X)                        38
    0x09, 0x31,  # ....Usage (Y)                        40
    0x15, 0x81,  # ....Logical Minimum (-127)           42
    0x25, 0x7f,  # ....Logical Maximum (127)            44
    0x75, 0x08,  # ....Report Size (8)                  46
    0x95, 0x02,  # ....Report Count (2)                 48
    0x81, 0x06,  # ....Input (Data,Var,Rel)             50
    0xc0,        # ...End Collection                    52
    0xc0,        # ..End Collection                     53
    0xc0,        # .End Collection                      54
]


linux_hidpp_rdesc = [
    0x05, 0x01,        # Usage Page (Generic Desktop)        0
    0x09, 0x06,        # Usage (Keyboard)                    2
    0xa1, 0x01,        # Collection (Application)            4
    0x85, 0x01,        #  Report ID (1)                      6
    0x95, 0x08,        #  Report Count (8)                   8
    0x75, 0x01,        #  Report Size (1)                    10
    0x15, 0x00,        #  Logical Minimum (0)                12
    0x25, 0x01,        #  Logical Maximum (1)                14
    0x05, 0x07,        #  Usage Page (Keyboard)              16
    0x19, 0xe0,        #  Usage Minimum (224)                18
    0x29, 0xe7,        #  Usage Maximum (231)                20
    0x81, 0x02,        #  Input (Data,Var,Abs)               22
    0x95, 0x06,        #  Report Count (6)                   24
    0x75, 0x08,        #  Report Size (8)                    26
    0x15, 0x00,        #  Logical Minimum (0)                28
    0x26, 0xff, 0x00,  #  Logical Maximum (255)              30
    0x05, 0x07,        #  Usage Page (Keyboard)              33
    0x19, 0x00,        #  Usage Minimum (0)                  35
    0x2a, 0xff, 0x00,  #  Usage Maximum (255)                37
    0x81, 0x00,        #  Input (Data,Arr,Abs)               40
    0x85, 0x0e,        #  Report ID (14)                     42
    0x05, 0x08,        #  Usage Page (LEDs)                  44
    0x95, 0x05,        #  Report Count (5)                   46
    0x75, 0x01,        #  Report Size (1)                    48
    0x15, 0x00,        #  Logical Minimum (0)                50
    0x25, 0x01,        #  Logical Maximum (1)                52
    0x19, 0x01,        #  Usage Minimum (1)                  54
    0x29, 0x05,        #  Usage Maximum (5)                  56
    0x91, 0x02,        #  Output (Data,Var,Abs)              58
    0x95, 0x01,        #  Report Count (1)                   60
    0x75, 0x03,        #  Report Size (3)                    62
    0x91, 0x01,        #  Output (Cnst,Arr,Abs)              64
    0xc0,              # End Collection                      66
    0x05, 0x01,        # Usage Page (Generic Desktop)        67
    0x09, 0x02,        # Usage (Mouse)                       69
    0xa1, 0x01,        # Collection (Application)            71
    0x85, 0x02,        #  Report ID (2)                      73
    0x09, 0x01,        #  Usage (Pointer)                    75
    0xa1, 0x00,        #  Collection (Physical)              77
    0x05, 0x09,        #   Usage Page (Button)               79
    0x19, 0x01,        #   Usage Minimum (1)                 81
    0x29, 0x10,        #   Usage Maximum (16)                83
    0x15, 0x00,        #   Logical Minimum (0)               85
    0x25, 0x01,        #   Logical Maximum (1)               87
    0x95, 0x10,        #   Report Count (16)                 89
    0x75, 0x01,        #   Report Size (1)                   91
    0x81, 0x02,        #   Input (Data,Var,Abs)              93
    0x05, 0x01,        #   Usage Page (Generic Desktop)      95
    0x16, 0x01, 0x80,  #   Logical Minimum (-32767)          97
    0x26, 0xff, 0x7f,  #   Logical Maximum (32767)           100
    0x75, 0x10,        #   Report Size (16)                  103
    0x95, 0x02,        #   Report Count (2)                  105
    0x09, 0x30,        #   Usage (X)                         107
    0x09, 0x31,        #   Usage (Y)                         109
    0x81, 0x06,        #   Input (Data,Var,Rel)              111
    0x15, 0x81,        #   Logical Minimum (-127)            113
    0x25, 0x7f,        #   Logical Maximum (127)             115
    0x75, 0x08,        #   Report Size (8)                   117
    0x95, 0x01,        #   Report Count (1)                  119
    0x09, 0x38,        #   Usage (Wheel)                     121
    0x81, 0x06,        #   Input (Data,Var,Rel)              123
    0x05, 0x0c,        #   Usage Page (Consumer Devices)     125
    0x0a, 0x38, 0x02,  #   Usage (AC Pan)                    127
    0x95, 0x01,        #   Report Count (1)                  130
    0x81, 0x06,        #   Input (Data,Var,Rel)              132
    0xc0,              #  End Collection                     134
    0xc0,              # End Collection                      135
    0x06, 0x00, 0xff,  # Usage Page (Vendor Defined Page 1)  136
    0x09, 0x01,        # Usage (Vendor Usage 1)              139
    0xa1, 0x01,        # Collection (Application)            141
    0x85, 0x10,        #  Report ID (16)                     143
    0x75, 0x08,        #  Report Size (8)                    145
    0x95, 0x06,        #  Report Count (6)                   147
    0x15, 0x00,        #  Logical Minimum (0)                149
    0x26, 0xff, 0x00,  #  Logical Maximum (255)              151
    0x09, 0x01,        #  Usage (Vendor Usage 1)             154
    0x81, 0x00,        #  Input (Data,Arr,Abs)               156
    0x09, 0x01,        #  Usage (Vendor Usage 1)             158
    0x91, 0x00,        #  Output (Data,Arr,Abs)              160
    0xc0,              # End Collection                      162
    0x06, 0x00, 0xff,  # Usage Page (Vendor Defined Page 1)  163
    0x09, 0x02,        # Usage (Vendor Usage 2)              166
    0xa1, 0x01,        # Collection (Application)            168
    0x85, 0x11,        #  Report ID (17)                     170
    0x75, 0x08,        #  Report Size (8)                    172
    0x95, 0x13,        #  Report Count (19)                  174
    0x15, 0x00,        #  Logical Minimum (0)                176
    0x26, 0xff, 0x00,  #  Logical Maximum (255)              178
    0x09, 0x02,        #  Usage (Vendor Usage 2)             181
    0x81, 0x00,        #  Input (Data,Arr,Abs)               183
    0x09, 0x02,        #  Usage (Vendor Usage 2)             185
    0x91, 0x00,        #  Output (Data,Arr,Abs)              187
    0xc0,              # End Collection                      189
    0x06, 0x00, 0xff,  # Usage Page (Vendor Defined Page 1)  190
    0x09, 0x04,        # Usage (Vendor Usage 0x04)           193
    0xa1, 0x01,        # Collection (Application)            195
    0x85, 0x20,        #  Report ID (32)                     197
    0x75, 0x08,        #  Report Size (8)                    199
    0x95, 0x0e,        #  Report Count (14)                  201
    0x15, 0x00,        #  Logical Minimum (0)                203
    0x26, 0xff, 0x00,  #  Logical Maximum (255)              205
    0x09, 0x41,        #  Usage (Vendor Usage 0x41)          208
    0x81, 0x00,        #  Input (Data,Arr,Abs)               210
    0x09, 0x41,        #  Usage (Vendor Usage 0x41)          212
    0x91, 0x00,        #  Output (Data,Arr,Abs)              214
    0x85, 0x21,        #  Report ID (33)                     216
    0x95, 0x1f,        #  Report Count (31)                  218
    0x15, 0x00,        #  Logical Minimum (0)                220
    0x26, 0xff, 0x00,  #  Logical Maximum (255)              222
    0x09, 0x42,        #  Usage (Vendor Usage 0x42)          225
    0x81, 0x00,        #  Input (Data,Arr,Abs)               227
    0x09, 0x42,        #  Usage (Vendor Usage 0x42)          229
    0x91, 0x00,        #  Output (Data,Arr,Abs)              231
    0xc0,              # End Collection                      233
]


@pytest.mark.parametrize(
    ('rdesc_raw', 'file'),
    [
        (simple_mouse_rdesc, 'simple-mouse-print.txt'),
        (linux_hidpp_rdesc, 'linux-hidpp-print.txt'),
    ],
)
def test_print(rdesc_raw, file):
    abs_file = os.path.abspath(os.path.join(__file__, '..', file))
    capture = io.StringIO()

    hid_parser.ReportDescriptor(rdesc_raw).print(file=capture)

    assert capture.getvalue() == open(abs_file, 'r').read()
