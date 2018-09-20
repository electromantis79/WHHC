# main.py -- put your code here!

import machine
import sys
import time
import pycom
import json
import _thread

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


def get_rssi_thread(wlan):
	global rssi, rssiThreadRunning
	before = time.ticks_ms()

	nets = wlan.scan()
	for net in nets:
		if net.ssid == 'ScoreNet':
			rssi = net.rssi
			print('RSSI =', rssi)
			rssi = str(rssi)[1:]
			rssi = int(rssi)
	after = time.ticks_ms()
	print('Send RSSI', str(rssi), '- took', str((after - before) / 1000), 'seconds')
	rssiThreadRunning = False


# Initialize ---------------------------------------------------

# Constants
HOST = '192.168.8.1'
PORT = 60032
SSID = 'ScoreNet'
AUTH = (WLAN.WPA2, 'centari008')

# Variables -------------------------------------------------------------

message = None
rssi = None
rssiThreadRunning = False
sendRssiCount = 0
SearchTimeoutDuration = 20
BatteryTimeoutDuration = 3
LongPressTimeoutDuration = 2.5
MainLoopFrequencyMs = 50
PowerOffSequenceFlag = True
PowerOnSequenceFlag = True
SearchBatteryTestModeFlag = False
ReceiverDiscoveredFlag = False
TransferFilesFlag = False
TransferFilesCompleteFlag = False
SocketConnectedFlag = False
mode = 'SearchModes'

# LED definitions ==========================================
LedDict = dict()
LedDict['P20'] = Pin('P20', mode=Pin.OUT)  # PIN_2  = LED_5 = topLed = PWM_1[5]
LedDict['P11'] = Pin('P11', mode=Pin.OUT)  # PIN_13 = LED_6 = signalLed
LedDict['P10'] = Pin('P10', mode=Pin.OUT)  # PIN_14 = LED_4 = strengthLedTop
LedDict['P9'] = Pin('P9', mode=Pin.OUT)  # PIN_15 = LED_3 = strengthLedMiddleTop
LedDict['P8'] = Pin('P8', mode=Pin.OUT)   # PIN_16 = LED_2 = strengthLedMiddleBottom
LedDict['P7'] = Pin('P7', mode=Pin.OUT)   # PIN_17 = LED_1 = strengthLedBottom
LedDict['P6'] = Pin('P6', mode=Pin.OUT)  # PIN_18 = LED_7 = batteryLed

# LedDict['P2'] = Pin('P2', mode = Pin.OUT)#WiPy Heartbeat pin
LedPinList = list(LedDict.keys())
# print('\nLedDict', LedDict)

# Turn all off
for x in LedPinList:
	LedDict[x].value(False)

led_sequence = LedSequences(LedDict)

# Build LedInfoDict ----------------------------------------
LedInfoDict = dict.fromkeys(LedPinList)
for pin in LedInfoDict:
	LedInfoDict[pin] = dict()

LedPinVsNumberList = [
	('P20', '5'), ('P11', '6'), ('P10', '4'), ('P9', '3'), ('P8', '2'), ('P7', '1'), ('P6', '7')]
for pin in LedPinVsNumberList:
	LedInfoDict[pin[0]]['led_id'] = pin[1]

LedPinVsKeypadPinList = [
	('P20', '2'), ('P11', '13'), ('P10', '14'), ('P9', '15'), ('P8', '16'), ('P7', '17'), ('P6', '18')]
for pin in LedPinVsKeypadPinList:
	LedInfoDict[pin[0]]['keypad_pin_number'] = pin[1]

LedPinVsFunctionNameList = [
	('P20', 'topLed'), ('P11', 'signalLed'), ('P10', 'strengthLedTop'), ('P9', 'strengthLedMiddleTop'),
	('P8', 'strengthLedMiddleBottom'), ('P7', 'strengthLedBottom'), ('P6', 'batteryLed')]
for pin in LedPinVsFunctionNameList:
	LedInfoDict[pin[0]]['function_name'] = pin[1]


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

ButtEventDict = dict.fromkeys(ButtPinList, 0)
# print('\nButtEventDict', ButtEventDict)

# Button Interrupts
for x in ButtPinList:
	ButtDict[x].callback(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=button_event)

machine.pin_deepsleep_wakeup(['P23'], machine.WAKEUP_ALL_LOW, enable_pull=True)


# Build ButtonInfoDict -----------------------------------
ButtonInfoDict = dict.fromkeys(ButtPinList)
for pin in ButtonInfoDict:
	ButtonInfoDict[pin] = dict()

ButtonPinVsNumberList = [
	('P23', '0'), ('P5', '1'), ('P4', '2'), ('P3', '3'), ('P18', '4'), ('P17', '5'), ('P16', '6'),
	('P15', '7'), ('P14', '8'), ('P13', '9')]
for pin in ButtonPinVsNumberList:
	ButtonInfoDict[pin[0]]['button_id'] = pin[1]

ButtonPinVsKeypadPinList = [
	('P23', '19'), ('P5', '4'), ('P4', '5'), ('P3', '6'), ('P18', '7'), ('P17', '8'), ('P16', '9'),
	('P15', '10'), ('P14', '11'), ('P13', '12')]
for pin in ButtonPinVsKeypadPinList:
	ButtonInfoDict[pin[0]]['keypad_pin_number'] = pin[1]

ButtonPinVsFunctionNameList = [
	('P23', 'modeButt'), ('P5', 'outPlusButt'), ('P4', 'strikePlusButt'), ('P3', 'ballPlusButt'),
	('P18', 'homeMinusButt'), ('P17', 'inningPlusButt'), ('P16', 'guestMinusButt'),
	('P15', 'homePlusButt'), ('P14', 'clockToggleButt'), ('P13', 'guestPlusButt')]
for pin in ButtonPinVsFunctionNameList:
	ButtonInfoDict[pin[0]]['function_name'] = pin[1]

# Translation dictionary for key names, correct this if pins ever change
KeyDict = {
	'P23': '10', 'P5': '9', 'P4': '8', 'P3': '7', 'P18': '6', 'P17': '5',
	'P16': '4', 'P15': '3', 'P14': '2', 'P13': '1'}
for pin in KeyDict:
	ButtonInfoDict[pin]['keypad_key_number'] = KeyDict[pin]

# Translation dictionary for key names, correct this if pins ever change
KeyMapDict = {
	'P23': 'E7', 'P5': 'D6', 'P4': 'D7', 'P3': 'D8', 'P18': 'C6', 'P17': 'C7', 'P16': 'C8', 'P15': 'B6',
	'P14': 'B7', 'P13': 'B8'}
for pin in KeyMapDict:
	ButtonInfoDict[pin]['keymap_grid_value'] = KeyMapDict[pin]


# Build JSON hierarchy ==========================================
JsonTreeDict = build_json_tree(LedDict, ButtDict, LedInfoDict, ButtonInfoDict)
# print('\nJsonTreeDict', JsonTreeDict)
'''
# Write tree.json file
with open('tree.json', 'w') as f:
	json_string = json.dumps(JsonTreeDict)
	f.write(json_string)
# print('\njson_string', json_string)
'''

# Timers
search_mode_timer = Timer.Chrono()
battery_mode_timer = Timer.Chrono()
long_press_timer = Timer.Chrono()

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
		time.sleep_ms(50)

		if ButtEventDict[button] == 1:
			# Down Press
			print('\nDown Press - LEDs on', button)
			ButtEventDict[button] = 2
			# Turn all on
			for x in LedPinList:
				LedDict[x].value(True)

		elif ButtEventDict[button] == 3:
			# Up Press
			print('\nUp Press', button)
			ButtEventDict[button] = 0
			print('\nRECOVER from Sleep Mode\n')
			# Turn all off
			for x in LedPinList:
				LedDict[x].value(False)
			break

# Test voltage sense function
vbatt = get_battery_voltage(1)

# LED Power On Sequence
led_sequence.timer.start()
while PowerOnSequenceFlag:
	PowerOnSequenceFlag = led_sequence.power_on(PowerOnSequenceFlag)
	machine.idle()
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
if machine.reset_cause() == machine.SOFT_RESET:
	print('Return from SOFT RESET')
	wlan = WLAN()
	print('Wireless still connected =', wlan.isconnected(), '\n')

else:
	print('Initialising WLAN in station mode...', end=' ')
	wlan = WLAN(mode=WLAN.STA)
	wlan.ifconfig(config=('192.168.8.145', '255.255.255.0', '192.168.8.1', '8.8.8.8'))
	print('done.\nConnecting to WiFi network...')
	wlan.connect(ssid=SSID, auth=AUTH)

search_mode_timer.start()
led_sequence.timer.start()

print('\n====== ENTERING MAIN LOOP ======')

# MAIN loop
while 1:
	machine.idle()
	time.sleep_ms(MainLoopFrequencyMs)

	if mode == 'SearchModes':

		# LED Sequences
		led_sequence.searching_for_receiver(not SearchBatteryTestModeFlag)
		led_sequence.battery_test(SearchBatteryTestModeFlag)

		# Search Mode Timer Check
		if search_mode_timer.read() > SearchTimeoutDuration:
			print('\nsearch_mode_timer triggered at ', search_mode_timer.read(), 's.')
			search_mode_timer.stop()
			search_mode_timer.reset()
			# ENTER Sleep Mode
			print('ENTER deep sleep\n')
			machine.deepsleep()

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
			search_mode_timer.stop()
			search_mode_timer.reset()
			search_mode_timer.start()

		# Handle button presses
		for button in ButtEventDict:
			if ButtEventDict[button] == 1:
				# Down Press
				print('\nDown Press', button)
				ButtEventDict[button] = 2
				long_press_timer.start()
				if button == 'P23':
					# MODE button
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
						print('\nENTER Search Mode')
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
						print('\n======== END Search Mode ========\n')
						print('\n======== BEGIN Power Off Sequence Mode ========\n')
						mode = 'PoweringDownMode'
						led_sequence.timer.stop()
						led_sequence.timer.reset()
						led_sequence.timer.start()
					else:
						long_press_timer.stop()
						print('\nLong press NOT detected at', long_press_timer.read(), 's.')
						long_press_timer.reset()

						print('search_mode_timer', search_mode_timer.read(), 's.')
						search_mode_timer.stop()
						search_mode_timer.reset()
						search_mode_timer.start()
						print('search_mode_timer after reset', search_mode_timer.read(), 's.')
				else:
					# Any other button
					print('search_mode_timer', search_mode_timer.read(), 's.')
					search_mode_timer.stop()
					search_mode_timer.reset()
					search_mode_timer.start()
					print('search_mode_timer after reset', search_mode_timer.read(), 's.')

		if wlan.isconnected() and mode != 'PoweringDownMode':

			if not SocketConnectedFlag:
				# Create and connect a socket
				try:
					# Create an AF_INET, STREAM socket (TCP)
					sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					print('Socket Created')

				except OSError as err:
					print("create_socket OS error:", err)
					print('Failed to create socket.')
					time.sleep_ms(500)
					machine.reset()

				try:
					sock.connect((HOST, PORT))
					sock.setblocking(0)
					print('Socket Connected to ' + HOST + ' on port ' + str(PORT))
					SocketConnectedFlag = True

				except OSError as err:
					print("connect_socket OS error:", err)
					print('Failed to connect to ' + HOST)
					sock.close()
					del sock
					time.sleep_ms(50)

			if SocketConnectedFlag:
				SocketConnectedFlag = False

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
			# TODO: add function here to check if we have a file to transfer
			if TransferFilesFlag:
				TransferFilesFlag = False
				mode = 'TransferMode'
				print('\n======== END Discovered Mode ========\n')
				print('\n======== BEGIN Transfer Mode ========\n')
				led_sequence.timer.stop()
				led_sequence.timer.reset()
				led_sequence.timer.start()
				# TODO: add thread here to transfer file with TransferFilesCompleteFlag
			else:
				mode = 'ConnectedMode'
				print('\n======== END Discovered Mode ========\n')
				print('\n======== BEGIN Connected Modes ========\n')
				led_sequence.timer.stop()
				led_sequence.timer.reset()

	elif mode == 'TransferMode':
		led_sequence.file_transfer(1)
		# TODO: should this sequence finish one cycle before moving on? YES

		if TransferFilesCompleteFlag and led_sequence.transfer_cycle_flag:
			TransferFilesCompleteFlag = False
			led_sequence.transfer_cycle_flag = False
			led_sequence.timer.stop()
			led_sequence.timer.reset()

			mode = 'ConnectedMode'
			print('\n======== END Transfer Mode ========\n')
			print('\n======== BEGIN Connected Modes ========\n')

	elif mode == 'ConnectedMode':
		# print('\nConnectedMode')

		# Handle button events
		JsonTreeDict, event_flag = handle_button_event(JsonTreeDict, ButtEventDict)

		# Send button events to server
		if event_flag:
			json_tree_fragment_dict = build_json_tree_fragment_dict(JsonTreeDict)
			sock, mode = send_events(sock, json_tree_fragment_dict, mode)

		# Check for data
		sock, data, mode = check_receive(sock, mode)

		# Format data
		if data:
			index_list = find_substrings(data, 'JSON_FRAGMENT')
			fragment_list = slice_fragments(data, index_list)
			for fragment_index, fragment in enumerate(fragment_list):
				fragment_list[fragment_index] = convert_to_json_format(fragment)

		# Process data
		if data:
			for fragment in fragment_list:
				check_led_data(fragment, LedDict)
				check_get_rssi_flag(fragment, JsonTreeDict)

		# React to data
		if JsonTreeDict['command_flags']['get_rssi']:
			if not rssiThreadRunning:
				time.sleep(0.5)
				rssiThreadRunning = True
				_thread.start_new_thread(get_rssi_thread, [wlan])
				print('after thread start', time.ticks_ms(), 'rssi =', rssi)
			else:
				if sendRssiCount >= 50:
					sendRssiCount = 0
					if rssi is not None:
						json_tree_fragment_dict = build_rssi_fragment_dict(rssi)
						sock, mode = send_events(sock, json_tree_fragment_dict, mode)
						print('rssi sent', time.ticks_ms())
				else:
					sendRssiCount += 1

		# Check connection to wifi and reconnect
		if not wlan.isconnected():
			mode = 'SearchModes'
			print('\n======== END Connected Modes ========\n')
			print('\n======== BEGIN Search Modes ========\n')

	elif mode == 'PoweringDownMode':
		PowerOffSequenceFlag = led_sequence.power_off(PowerOffSequenceFlag)

		if not PowerOffSequenceFlag:
			mode = 'SleepMode'
			print('\n======== END Powering Down Mode ========\n')
			print('\n======== BEGIN Sleep Mode ========\n')

	elif mode == 'SleepMode':
		print('ENTER deep sleep\n')
		machine.deepsleep()
	else:
		print('ERROR - no mode selected area should never be entered')
