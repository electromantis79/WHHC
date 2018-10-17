# boot.py -- run on boot-up
# can run arbitrary Python, but best to keep it minimal

# BEGIN Boot Up Mode ===============================

import os
import machine
import sys
import time

from machine import UART
from machine import Pin
from os import dupterm

# Functions using global must be in this file to call them from this file for some reason


def button_event(pin):  # Pin Callback
	global ButtEventDict
	if pin.id() in ButtEventDict:
		last_state = ButtEventDict[pin.id()]
		# Down press = 1, Up press = 2
		# print('---------------------------', pin.id(), pin())
		# print('ButtEventDict[pin.id()]', last_state)
		if last_state == 0 and pin() == 0:
			last_state = 1
		elif last_state == 2 and pin() == 1:
			last_state = 3

		ButtEventDict[pin.id()] = last_state
		# print('ButtEventDict[pin.id()]', last_state)


# enable the UART on the USB-to-serial port
uart = UART(0, baudrate=115200)

# duplicate the terminal on the UART
dupterm(uart)

print('\nFirst possible time display', time.ticks_us() / 1000, 'ms')

print('\nUART initialised')
print('\n======== BEGIN Boot Up Mode ========\n')

print(os.uname())
print('\nPython version', sys.version)
print('Unique ID', machine.unique_id(), 'Frequency', machine.freq())


print('\nAfter boot messages', time.ticks_us() / 1000, 'ms')

# LED definitions ==========================================
LedDict = dict()
LedDict['P20'] = Pin('P20', mode=Pin.OUT)  # PIN_2  = LED_5 = topLed = PWM_1[5]
LedDict['P11'] = Pin('P11', mode=Pin.OUT)  # PIN_13 = LED_6 = signalLed
LedDict['P10'] = Pin('P10', mode=Pin.OUT)  # PIN_14 = LED_4 = strengthLedTop
LedDict['P9'] = Pin('P9', mode=Pin.OUT)  # PIN_15 = LED_3 = strengthLedMiddleTop
LedDict['P8'] = Pin('P8', mode=Pin.OUT)   # PIN_16 = LED_2 = strengthLedMiddleBottom
LedDict['P7'] = Pin('P7', mode=Pin.OUT)   # PIN_17 = LED_1 = strengthLedBottom
LedDict['P6'] = Pin('P6', mode=Pin.OUT)  # PIN_18 = LED_7 = batteryLed
# print('\nLedDict', LedDict)

# LedDict['P2'] = Pin('P2', mode = Pin.OUT)#WiPy Heartbeat pin

LedPinList = list(LedDict.keys())

print('\nAfter LedDict', time.ticks_us() / 1000, 'ms')

# 10-Button Baseball Keypad definitions ===================
ButtDict = dict()
ButtDict['P23'] = Pin(
	'P23', mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_19 = BUTT_0 = KEY_10 = modeButt
ButtDict['P5'] = Pin(
	'P5', mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_4 = BUTT_1 = KEY_9 = outPlusButt = CX_DETECT
ButtDict['P4'] = Pin(
	'P4', mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_5 = BUTT_2 = KEY_8 = strikePlusButt =  = LED2_IN
ButtDict['P3'] = Pin(
	'P3', mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_6 = BUTT_3 = KEY_7 = ballPlusButt = PIC_RX2/LED1_IN
ButtDict['P18'] = Pin(
	'P18', mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_7 = BUTT_4 = KEY_6 = homeMinusButt = RUN
ButtDict['P17'] = Pin(
	'P17', mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_8 = BUTT_5 = KEY_5 = inningPlusButt = STOP
ButtDict['P16'] = Pin(
	'P16', mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_9 = BUTT_6 = KEY_4 = guestMinusButt = RUN/STOP CLOCK
ButtDict['P15'] = Pin(
	'P15', mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_10 = BUTT_7 = KEY_3 = homePlusButt = RUN/STOP DGT
ButtDict['P14'] = Pin(
	'P14', mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_11 = BUTT_8 = KEY_2 = clockToggleButt = RESET 2
ButtDict['P13'] = Pin(
	'P13', mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_12 = BUTT_9 = KEY_1 = guestPlusButt = RESET 1
ButtPinList = list(ButtDict.keys())
# print('\nButtDict', ButtDict, '\nButtPinList', ButtPinList)

print('\nAfter ButtDict', time.ticks_us() / 1000, 'ms')

ButtEventDict = dict.fromkeys(ButtPinList, 0)
# print('\nButtEventDict', ButtEventDict)

# Button Interrupts
for x in ButtPinList:
	ButtDict[x].callback(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=button_event)

machine.pin_deepsleep_wakeup(['P23'], machine.WAKEUP_ALL_LOW, enable_pull=True)

print('\nAfter button interrupts', time.ticks_us() / 1000, 'ms')

if machine.reset_cause() == machine.DEEPSLEEP_RESET:
	# sleep if button not being held then continue on release
	print('\nReturn from DEEP SLEEP')
	if not ButtDict['P23'].value():
		button = 'P23'
		ButtEventDict[button] = 1
	else:
		print('ENTER deep sleep AGAIN\n')
		machine.deepsleep()

	while 1:
		machine.idle()
		time.sleep_ms(10)

		if ButtEventDict[button] == 1:
			# Down Press
			print('\nDown Press - LEDs on', button, time.ticks_us() / 1000, 'ms')
			ButtEventDict[button] = 2
			# Turn all on
			for x in LedPinList:
				LedDict[x].value(True)

		elif ButtEventDict[button] == 3:
			# Up Press
			ButtEventDict[button] = 0
			print('\nUp Press', button, time.ticks_us() / 1000, 'ms')
			print('\nRECOVER from Sleep Mode', time.ticks_us() / 1000, 'ms\n')
			break
