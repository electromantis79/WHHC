# main.py -- put your code here!

import machine
import sys
import time
import pycom

from network import WLAN
from machine import Pin
from machine import Timer
from utils import *
from led_sequences import LedSequences


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


# Initialize ---------------------------------------------------

# Constants
HOST = '192.168.8.1'
PORT = 60032
SSID = 'ScoreNet'
AUTH = (WLAN.WPA2, 'centari008')

# Variables -------------------------------------------------------------

message = None
rssi = None
SearchTimeoutDuration = 8
BatteryTimeoutDuration = 3
LongPressTimeoutDuration = 2.5
PowerOffSequenceFlag = False
PowerOnSequenceFlag = True
SearchBatteryTestModeFlag = False
ReceiverDiscoveredFlag = False
mode = 'SearchModes'

# LED definitions
LedDict = {}
LedDict['P13'] = Pin(Pin.exp_board.G5, mode=Pin.OUT)  # PIN_1  = LED_5 = topLed = PWM_1[5]
LedDict['P18'] = Pin(Pin.exp_board.G30, mode=Pin.OUT)  # PIN_13 = LED_6 = signalLed
LedDict['P17'] = Pin(Pin.exp_board.G31, mode=Pin.OUT)  # PIN_14 = LED_4 = strengthLedTop
# LedDict['P16'] = Pin(Pin.exp_board.G3, mode=Pin.OUT)  # PIN_15 = LED_3 = strengthLedMiddleTop
LedDict['P15'] = Pin(Pin.exp_board.G0, mode=Pin.OUT)   # PIN_16 = LED_2 = strengthLedMiddleBottom
LedDict['P14'] = Pin(Pin.exp_board.G4, mode=Pin.OUT)   # PIN_17 = LED_1 = strengthLedBottom
LedDict['P19'] = Pin(Pin.exp_board.G6, mode=Pin.OUT)  # PIN_18 = LED_7 = batteryLed

# LedDict['P2'] = Pin(Pin.module.P2, mode = Pin.OUT)#WiPy Heartbeat pin
LedPinList = list(LedDict.keys())
print('\nLedDict', LedDict)

# Turn all off
for x in LedPinList:
	LedDict[x].value(False)

led_sequence = LedSequences(LedDict)

# 10-Button Baseball Keypad
ButtDict = {}
ButtDict['P23'] = Pin(
	Pin.exp_board.G10, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_19 = BUTT_0 = KEY_10 = modeButt
ButtDict['P11'] = Pin(
	Pin.exp_board.G22, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_4 = BUTT_1 = KEY_9 = outPlusButt = CX_DETECT
ButtDict['P10'] = Pin(
	Pin.exp_board.G17, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_5 = BUTT_2 = KEY_8 = strikePlusButt =  = LED2_IN
# BUTTON ON EXPANSION BOARD

ButtDict['P9'] = Pin(
	Pin.exp_board.G16, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_6 = BUTT_3 = KEY_7 = ballPlusButt = PIC_RX2/LED1_IN
ButtDict['P8'] = Pin(
	Pin.exp_board.G15, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_7 = BUTT_4 = KEY_6 = homeMinusButt = RUN
ButtDict['P7'] = Pin(
	Pin.exp_board.G14, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_8 = BUTT_5 = KEY_5 = inningPlusButt = STOP
ButtDict['P6'] = Pin(
	Pin.exp_board.G13, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_9 = BUTT_6 = KEY_4 = guestMinusButt = RUN/STOP CLOCK
ButtDict['P5'] = Pin(
	Pin.exp_board.G12, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_10 = BUTT_7 = KEY_3 = homePlusButt = RUN/STOP DGT
ButtDict['P4'] = Pin(
	Pin.exp_board.G11, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_11 = BUTT_8 = KEY_2 = clockToggleButt = RESET 2
ButtDict['P3'] = Pin(
	Pin.exp_board.G24, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_12 = BUTT_9 = KEY_1 = guestPlusButt = RESET 1
ButtPinList = list(ButtDict.keys())
print('\nButtDict', ButtDict, '\nButtPinList', ButtPinList)

ButtEventDict = dict.fromkeys(ButtPinList, 0)
print('\nButtEventDict', ButtEventDict)


# Pin dictionary and its reverse used to get pin id string out of callback
PinDict = {}
PinList = []
PinList.extend(LedPinList)
PinList.extend(ButtPinList)
print('\nPinList', PinList)
PinRange = range(len(PinList))
for x, y in enumerate(PinList):
	PinDict[y] = PinRange[x]
print('\nPinDict', PinDict)
PinDictReverse = {}
for x, y in enumerate(PinRange):
	PinDictReverse[y] = PinList[x]
print('\nPinDictReverse', PinDictReverse)

# Translation dictionary for key names, correct this if pins ever change
KeyDict = {
	'P23': 'KEY_10', 'P11': 'KEY_9', 'P10': 'KEY_8', 'P9': 'KEY_7', 'P8': 'KEY_6', 'P7': 'KEY_5',
	'P6': 'KEY_4', 'P5': 'KEY_3', 'P4': 'KEY_2', 'P3': 'KEY_1'}
print('\nKeyDict', KeyDict)

# Translation dictionary for key names, correct this if pins ever change
KeyMapDict = {
	'P23': 'E7', 'P11': 'D6', 'P10': 'D7', 'P9': 'D8', 'P8': 'C6', 'P7': 'C7', 'P6': 'C8', 'P5': 'B6',
	'P4': 'B7', 'P3': 'B8'}
print('\nKeyMapDict', KeyMapDict)

# Button Interrupts
for x in ButtPinList:
	ButtDict[x].callback(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=button_event)

# Timers
search_mode_timer = Timer.Chrono()
battery_mode_timer = Timer.Chrono()
long_press_timer = Timer.Chrono()

# Test voltage sense function
vbatt = get_battery_voltage(1)

# LED Power On Sequence
led_sequence.timer.start()
while PowerOnSequenceFlag:
	PowerOnSequenceFlag = led_sequence.power_on(PowerOnSequenceFlag)
	time.sleep_ms(50)

# Clear any button presses
for button in ButtEventDict:
	ButtEventDict[button] = 0

# Change LED from flashing blue default to solid red
pycom.heartbeat(False)
pycom.rgbled(0xff0000)

# END Boot Up Mode -----------------------

print('\n======== END Boot Up Mode ========')
print('\n======== BEGIN Search Mode ========\n')

# Search Mode ============================

mode = 'SearchModes'

# Wifi connection
if machine.reset_cause() != machine.SOFT_RESET:
	print('Initialising WLAN in station mode...', end=' ')
	wlan = WLAN(mode=WLAN.STA)
	wlan.ifconfig(config=('192.168.8.145', '255.255.255.0', '192.168.8.1', '8.8.8.8'))
	print('done.\nConnecting to WiFi network...')
	wlan.connect(ssid=SSID, auth=AUTH)

else:
	# machine.SOFT_RESET
	wlan = WLAN()
	print('Wireless still initialized =', wlan.isconnected(), '\n')

search_mode_timer.start()
led_sequence.timer.start()

print('\n====== ENTERING MAIN LOOP ======')

# MAIN loop
while 1:
	machine.idle()
	time.sleep_ms(50)

	if mode == 'BootUp':
		PowerOnSequenceFlag = led_sequence.power_on(PowerOnSequenceFlag)
		if not PowerOnSequenceFlag:
			mode = 'SearchModes'
			search_mode_timer.start()
			led_sequence.timer.start()

	elif mode == 'SearchModes':

		# LED Sequences
		PowerOffSequenceFlag = led_sequence.power_off(PowerOffSequenceFlag)
		led_sequence.searching_for_receiver(not SearchBatteryTestModeFlag)
		led_sequence.battery_test(SearchBatteryTestModeFlag)

		# Search Mode Timer Check
		if search_mode_timer.read() > SearchTimeoutDuration:
			print('\nsearch_mode_timer triggered at ', search_mode_timer.read(), 's.')
			search_mode_timer.stop()
			search_mode_timer.reset()
		# ENTER Sleep Mode

		# Battery Mode Timer Check
		if battery_mode_timer.read() > BatteryTimeoutDuration:
			print('\nsearch_mode_timer triggered at ', battery_mode_timer.read(), 's.')
			battery_mode_timer.stop()
			battery_mode_timer.reset()
			led_sequence.timer.start()
			# ENTER Search Mode
			SearchBatteryTestModeFlag = False
			print('\n======== END Search Battery Test Mode ========\n')
			print('\n======== BEGIN Search Mode ========\n')

		if not PowerOffSequenceFlag:
			# Handle button presses
			for button in ButtEventDict:
				if ButtEventDict[button] == 1:
					# Down Press
					print('\nDown Press', button)
					ButtEventDict[button] = 2
					if button == 'P23':
						# MODE button
						long_press_timer.start()
						search_mode_timer.stop()
						search_mode_timer.reset()
						# TOGGLE Search Mode and Search Battery Test Mode
						if not SearchBatteryTestModeFlag:
							print('\nENTER Search Battery Test Mode')
							SearchBatteryTestModeFlag = True
							battery_mode_timer.start()
							led_sequence.timer.stop()
							led_sequence.timer.reset()
							print('\n======== END Search Mode ========\n')
							print('\n======== BEGIN Search Battery Test Mode ========\n')
						else:
							print('\nENTER Search Battery Test Mode')
							SearchBatteryTestModeFlag = False
							battery_mode_timer.stop()
							battery_mode_timer.reset()
							search_mode_timer.start()
							led_sequence.timer.start()
							print('\n======== END Search Battery Test Mode ========\n')
							print('\n======== BEGIN Search Mode ========\n')
					else:
						# Any other button
						print('search_mode_timer', search_mode_timer.read(), 's.')
						search_mode_timer.reset()
						print('search_mode_timer after reset', search_mode_timer.read(), 's.')
						if SearchBatteryTestModeFlag:
							print('\nENTER Search Battery Test Mode')
							SearchBatteryTestModeFlag = False
							battery_mode_timer.stop()
							battery_mode_timer.reset()
							search_mode_timer.start()
							led_sequence.timer.start()
							print('\n======== END Search Battery Test Mode ========\n')
							print('\n======== BEGIN Search Mode ========\n')

				elif ButtEventDict[button] == 3:
					# Up Press
					print('\nUp Press', button)
					ButtEventDict[button] = 0
					if button == 'P23':
						# MODE button
						if long_press_timer.read() > LongPressTimeoutDuration:
							print('\nLong press detected at', long_press_timer.read(), 's.')
							long_press_timer.stop()
							long_press_timer.reset()
							# ENTER Sleep Mode with Power Off Sequence
							print('\nENTER Sleep Mode with Power Off Sequence\n')
							PowerOffSequenceFlag = True
							led_sequence.timer.start()
						else:
							long_press_timer.stop()
							print('\nLong press NOT detected at', long_press_timer.read(), 's.')
							long_press_timer.reset()

							print('search_mode_timer', search_mode_timer.read(), 's.')
							search_mode_timer.reset()
							print('search_mode_timer after reset', search_mode_timer.read(), 's.')
					else:
						# Any other button
						print('search_mode_timer', search_mode_timer.read(), 's.')
						search_mode_timer.reset()
						print('search_mode_timer after reset', search_mode_timer.read(), 's.')

		if wlan.isconnected():
			# Create and connect a socket
			sock = connect_socket(HOST, PORT)

			mode = 'DiscoveredMode'
			long_press_timer.stop()
			long_press_timer.reset()
			search_mode_timer.stop()
			search_mode_timer.reset()
			battery_mode_timer.stop()
			battery_mode_timer.reset()
			led_sequence.timer.stop()
			led_sequence.timer.reset()
			ip, mask, gateway, dns = wlan.ifconfig()
			print('IP address: ', ip)
			print('Netmask:    ', mask)
			print('Gateway:    ', gateway)
			print('DNS:        ', dns)
			print()
			led_sequence.timer.start()
			print('\n======== END Search Modes ========\n')
			print('\n======== BEGIN Discovered Mode ========\n')
			ReceiverDiscoveredFlag = True

	elif mode == 'DiscoveredMode':
		ReceiverDiscoveredFlag = led_sequence.receiver_discovered(ReceiverDiscoveredFlag)
		if not ReceiverDiscoveredFlag:
			mode = 'TransferMode'
			print('\n======== END Discovered Mode ========\n')
			print('\n======== BEGIN Transfer Mode ========\n')

	elif mode == 'TransferMode':
		mode = 'ConnectedMode'
		print('\n======== END Transfer Mode ========\n')
		print('\n======== BEGIN Connected Modes ========\n')

	elif mode == 'ConnectedMode':

		# Send button press to server
		sock, message = send_button_press(sock, HOST, PORT, ButtEventDict, KeyMapDict)

		# Check for data
		sock, data = check_receive(sock, HOST, PORT)

		# Check effect of received data

		# Check connection to wifi and reconnect
		if not wlan.isconnected():
			mode = 'SearchModes'

	elif mode == 'PoweringDownMode':
		pass
	elif mode == 'SleepMode':
		pass
	else:
		print('ERROR - no mode selected area should never be entered')
