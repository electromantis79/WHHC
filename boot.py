# boot.py -- run on boot-up
# can run arbitrary Python, but best to keep it minimal

# BEGIN Boot Up Mode ===============================

import os
import machine
import sys

from machine import UART
from os import dupterm

# enable the UART on the USB-to-serial port
uart = UART(0, baudrate=115200)

# duplicate the terminal on the UART
dupterm(uart)

print('\nUART initialised')
print('\n======== BEGIN Boot Up Mode ========\n')

print(os.uname())
print('\nPython version', sys.version)
print('Unique ID', machine.unique_id(), 'Frequency', machine.freq())
