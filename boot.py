# boot.py -- run on boot-up

import time
boot_start_time = time.ticks_us() / 1000
print('\nTop of boot.py before imports', boot_start_time, 'ms')

# BEGIN Boot Up Mode ===============================

import os
import machine
import sys

# Functions using global must be in this file to call them from this file for some reason


def button_event(pin):  # Pin Callback
	global PreviousButtonValueDict, offset, button_event_buffer, block_presses_flag, button_event_print_flag

	event_time = time.ticks_us()
	current_value = pin()
	button_name = pin.id()
	if button_name in PreviousButtonValueDict:
		previous_value = PreviousButtonValueDict[button_name]

		if button_event_print_flag:
			print(
				'\n----START CALLBACK',
				'\n\n    button_name =', button_name, ', previous_value =', previous_value,
				', current_value =', current_value)

		if not block_presses_flag:
			load_buffer = False

			# Find direction
			if previous_value == 1 and current_value == 0:  # FALLING
				if button_event_print_flag:
					print('\n    falling_time', event_time / 1000, 'ms')
				load_buffer = True

			elif previous_value == 0 and current_value == 1:  # RISING
				if button_event_print_flag:
					print('\n    rising_time', event_time / 1000)
				load_buffer = True

			else:
				if button_event_print_flag:
					print('\n    NO TRANSITION!!!!', event_time / 1000, 'ms')

			if load_buffer:
				packet = (button_name, current_value, event_time - offset)
				button_event_buffer.append(packet)

			PreviousButtonValueDict[button_name] = current_value

		else:
			if button_event_print_flag:
				print('\n    block_presses_flag', True)

		event_end_time = time.ticks_us()
		if button_event_print_flag:
			print('    function time', (event_end_time - event_time) / 1000, 'ms')
			print('\n----END CALLBACK')


# enable the UART on the USB-to-serial port
uart = machine.UART(0, baudrate=115200)

# duplicate the terminal on the UART
os.dupterm(uart)

print('\nUART initialised')

import_end_time = time.ticks_us() / 1000
print('\nAfter imports', import_end_time, 'ms, Dif imports', import_end_time - boot_start_time, 'ms')

print('\n======== BEGIN Boot Up Mode ========\n')

print(os.uname())
print('\nPython version', sys.version)
print('Unique ID', machine.unique_id(), 'Frequency', machine.freq())

print('\nAfter boot messages', time.ticks_us() / 1000, 'ms')

# Initial variables
offset = 0
button_event_buffer = []
block_presses_flag = False
button_event_print_flag = True
deep_down_flag = False

# LED definitions ==========================================
LedDict = dict()
LedDict['P20'] = machine.Pin('P20', mode=machine.Pin.OUT)  # PIN_2  = LED_5 = topLed = PWM_1[5]
LedDict['P11'] = machine.Pin('P11', mode=machine.Pin.OUT)  # PIN_13 = LED_6 = signalLed
LedDict['P10'] = machine.Pin('P10', mode=machine.Pin.OUT)  # PIN_14 = LED_4 = strengthLedTop
LedDict['P9'] = machine.Pin('P9', mode=machine.Pin.OUT)  # PIN_15 = LED_3 = strengthLedMiddleTop
LedDict['P8'] = machine.Pin('P8', mode=machine.Pin.OUT)   # PIN_16 = LED_2 = strengthLedMiddleBottom
LedDict['P7'] = machine.Pin('P7', mode=machine.Pin.OUT)   # PIN_17 = LED_1 = strengthLedBottom
LedDict['P6'] = machine.Pin('P6', mode=machine.Pin.OUT)  # PIN_18 = LED_7 = batteryLed
# print('\nLedDict', LedDict)

# LedDict['P2'] = machine.Pin('P2', mode = machine.Pin.OUT)#WiPy Heartbeat pin

LedPinList = list(LedDict.keys())

print('\nAfter LedDict', time.ticks_us() / 1000, 'ms')

# 10-Button Baseball Keypad definitions ===================
ButtDict = dict()
ButtDict['P23'] = machine.Pin(
	'P23', mode=machine.Pin.IN, pull=machine.Pin.PULL_UP)  # PIN_19 = BUTT_0 = KEY_10 = modeButt
ButtDict['P5'] = machine.Pin(
	'P5', mode=machine.Pin.IN, pull=machine.Pin.PULL_UP)  # PIN_4 = BUTT_1 = KEY_9 = outPlusButt = CX_DETECT
ButtDict['P4'] = machine.Pin(
	'P4', mode=machine.Pin.IN, pull=machine.Pin.PULL_UP)  # PIN_5 = BUTT_2 = KEY_8 = strikePlusButt =  = LED2_IN
ButtDict['P3'] = machine.Pin(
	'P3', mode=machine.Pin.IN, pull=machine.Pin.PULL_UP)  # PIN_6 = BUTT_3 = KEY_7 = ballPlusButt = PIC_RX2/LED1_IN
ButtDict['P18'] = machine.Pin(
	'P18', mode=machine.Pin.IN, pull=machine.Pin.PULL_UP)  # PIN_7 = BUTT_4 = KEY_6 = homeMinusButt = RUN
ButtDict['P17'] = machine.Pin(
	'P17', mode=machine.Pin.IN, pull=machine.Pin.PULL_UP)  # PIN_8 = BUTT_5 = KEY_5 = inningPlusButt = STOP
ButtDict['P16'] = machine.Pin(
	'P16', mode=machine.Pin.IN, pull=machine.Pin.PULL_UP)  # PIN_9 = BUTT_6 = KEY_4 = guestMinusButt = RUN/STOP CLOCK
ButtDict['P15'] = machine.Pin(
	'P15', mode=machine.Pin.IN, pull=machine.Pin.PULL_UP)  # PIN_10 = BUTT_7 = KEY_3 = homePlusButt = RUN/STOP DGT
ButtDict['P14'] = machine.Pin(
	'P14', mode=machine.Pin.IN, pull=machine.Pin.PULL_UP)  # PIN_11 = BUTT_8 = KEY_2 = clockToggleButt = RESET 2
ButtDict['P13'] = machine.Pin(
	'P13', mode=machine.Pin.IN, pull=machine.Pin.PULL_UP)  # PIN_12 = BUTT_9 = KEY_1 = guestPlusButt = RESET 1
ButtPinList = list(ButtDict.keys())
# print('\nButtDict', ButtDict, '\nButtPinList', ButtPinList)

PreviousButtonValueDict = dict.fromkeys(ButtPinList, 1)

print('\nAfter ButtDict', time.ticks_us() / 1000, 'ms')

# Button Interrupts
for x in ButtPinList:
	ButtDict[x].callback(trigger=machine.Pin.IRQ_FALLING | machine.Pin.IRQ_RISING, handler=button_event)

print('\nAfter button interrupts', time.ticks_us() / 1000, 'ms')

machine.pin_deepsleep_wakeup(['P23'], machine.WAKEUP_ALL_LOW, enable_pull=True)

if machine.reset_cause() == machine.DEEPSLEEP_RESET:
	# sleep if button not being held then continue on release
	print('\nReturn from DEEP SLEEP')
	mode_button = 'P23'
	if not ButtDict[mode_button].value():
		deep_down_flag = True
	else:
		print('ENTER deep sleep AGAIN\n')
		machine.deepsleep()

	while 1:
		machine.idle()
		time.sleep_ms(10)

		if deep_down_flag:
			deep_down_flag = False
			# Down Press
			print('\nDown Press - LEDs on', mode_button, time.ticks_us() / 1000, 'ms')

			# Turn all on
			for x in LedPinList:
				LedDict[x].value(True)

		if ButtDict[mode_button].value():
			# Up Press
			print('\nUp Press', mode_button, time.ticks_us() / 1000, 'ms')
			print('\nRECOVER from Sleep Mode', time.ticks_us() / 1000, 'ms\n')
			break

boot_end_time = time.ticks_us() / 1000
print('\nEND of boot.py', boot_end_time, 'ms, Dif boot.py', boot_end_time - boot_start_time, 'ms')
