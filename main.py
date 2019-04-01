# main.py -- put your code here!

import machine
import sys
import time
import pycom
import micropython
import json
import _thread

from network import WLAN
from machine import Pin
from machine import Timer
from utils import *
from led_sequences import LedSequences

print('\nTop of main.py after imports', time.ticks_us() / 1000, 'ms')

# Functions using global must be in the main.py file for some reason


def handle_button_event_thread():
	global ButtEventDict, mode, JsonTreeDict, offset, darkFlag, sock,\
		printFlag, buttonThreadFrequency, need_acknowledgement_flag, block_presses_flag
	nothing_pressed = True
	while 1:
		machine.idle()
		time.sleep_ms(buttonThreadFrequency)
		if mode == 'ConnectedMode':

			# Handle button events
			tic = time.ticks_us() / 1000
			# print('--Event START', tic, 'ms')

			if not block_presses_flag:
				JsonTreeDict, event_flag = handle_button_event(JsonTreeDict, ButtEventDict, offset)

				# Send button events to server
				if event_flag:
					toc = time.ticks_us() / 1000
					if printFlag:
						print('Event FLAG', toc, 'ms')
					# connected_mode_power_down_timer.stop()
					# connected_mode_power_down_timer.reset()
					# connected_mode_power_down_timer.start()
					# darkFlag = False
					json_tree_fragment_dict = build_json_tree_fragment_dict(JsonTreeDict)
					need_acknowledgement_flag, sock, mode = send_events(sock, json_tree_fragment_dict, mode, print_flag=printFlag)
					toc2 = time.ticks_us() / 1000
					if printFlag:
						print('--Event END', toc2, 'ms,', 'Dif check tree', toc-tic, 'ms,', 'Dif full send', toc2-tic, 'ms\n')


def get_rssi_thread(wlan):
	global rssi, rssiThreadRunning
	before = time.ticks_ms()
	time.sleep_ms(200)  # Gives time for received packets to be parsed between threads

	nets = wlan.scan()
	for net in nets:
		if net.ssid == 'ScoreNet':
			rssi = net.rssi
			print('Scorenet found with RSSI =', rssi)
			rssi = str(rssi)[1:]
			rssi = int(rssi)
	after = time.ticks_ms()
	print('rssi thread took', str((after - before) / 1000), 'seconds')
	rssiThreadRunning = False


def send_blocks_thread():
	global sendBlocksFlag, sock, mode, block_data, need_acknowledgement_flag
	block_data = 'dfgdfg45345dfgdfgd4sdg8sdgj348u'
	Steps = 4
	Transmits = 4
	steps = Steps
	transmits = Transmits
	while sendBlocksFlag:
		while steps and sendBlocksFlag:
			while transmits and sendBlocksFlag:
				stamp = str(get_ticks_us(offset))
				message = block_data + '@' + str(steps) + '@' + stamp + '@' + str(transmits)
				need_acknowledgement_flag, sock, mode = send_events(sock, message, mode)
				time.sleep_ms(100)
				transmits -= 1
				machine.idle()

			block_data = block_data + block_data
			transmits = Transmits
			steps -= 1
			time.sleep_ms(2000)
			machine.idle()

		machine.idle()
		sendBlocksFlag = False

	print('send_blocks_thread END')


def ptp_thread():
	global ptp_sock, PtpSocketConnectedFlag, timePin, offset, ptp_thread_flag
	ptp_thread_flag = True
	sync_string = 'SYNC'
	follow_up_string = 'FOLLOW_UP'
	delay_request_string = 'DELAY_REQUEST'
	delay_response_string = 'DELAY_RESPONSE'
	sync_flag = False
	follow_up_flag = False
	delay_response_flag = False
	time_1 = None
	time_2 = None
	time_3 = None
	time_4 = None
	offsetList = []
	offsetCount = 0
	check_socket_count = 0
	print_ptp_messages = False
	while 1:
		if PtpSocketConnectedFlag and ptp_sock is not None:
			data = None
			try:
				data = ptp_sock.read()
				read_time = time.ticks_us()

			except OSError as err:
				# print (err, err.errno)

				if err.errno == 11:
					# Don't care about error here. It is normal for .recv() if non-blocking to wait for device to be ready
					print('special 11 spot', err)
				elif err.errno == 113:
					print("check_receive OS error:", err)
				elif err.errno == 104:  # ECONNRESET
					print("check_receive OS error ECONNRESET:", err)
				else:
					print("check_receive OS error GENERIC:", err)

				ptp_sock.close()
				PtpSocketConnectedFlag = False

			if data is not None:
				data = decode_bytes_to_string(data)

			if data:
				if print_ptp_messages:
					print('\nData Received', read_time, 'us:', data)
				check_socket_count = 0

				if data[:len(sync_string)] == sync_string:
					valid, time_stamp = validate_ptp_string(data, sync_string, print_messages=print_ptp_messages)
					if valid:
						sync_flag = True
						time_2 = read_time
						timePin.value(True)  # This is redundant in next function but is here for faster toggle
						toggle_pin_ms(timePin, repeat_quantity=2)
						if print_ptp_messages:
							print('time_2=', time_2)

						estimated_time = time_stamp
						if print_ptp_messages:
							print('estimated_time', estimated_time)
					else:
						sync_flag = False
						follow_up_flag = False
						delay_response_flag = False

				elif data[:len(follow_up_string)] == follow_up_string:
					valid, time_stamp = validate_ptp_string(data, follow_up_string, print_messages=print_ptp_messages)
					if valid:
						follow_up_flag = True
						time_1 = time_stamp
						guess = time.ticks_us() - offset
						# print('time_1=', time_1, 'guess', guess, 'diff guess', guess - time_1)

						try:
							# Send the whole string
							ptp_sock.sendall(delay_request_string + ' ' + str(guess + 7000))
							time_3 = time.ticks_us()

							timePin.value(True)  # This is redundant in next function but is here for faster toggle
							toggle_pin_ms(timePin, repeat_quantity=3)
							if print_ptp_messages:
								print('time_3=', time_3)

							if print_ptp_messages:
								print('\nSent', time_3, 'us:', delay_request_string)

						except OSError as err:
							if err.errno == 104:  # ECONNRESET
								print("send_button_events OS error ECONNRESET:", err)
							else:
								print("send_button_events OS error:", err)
					else:
						sync_flag = False
						follow_up_flag = False
						delay_response_flag = False

				elif data[:len(delay_response_string)] == delay_response_string:
					valid, time_stamp = validate_ptp_string(data, delay_response_string, print_messages=print_ptp_messages)
					if valid:
						delay_response_flag = True
						time_4 = time_stamp
						if print_ptp_messages:
							print('time_4=', time_4)

					else:
						sync_flag = False
						follow_up_flag = False
						delay_response_flag = False

				if (
						sync_flag and follow_up_flag and delay_response_flag and
						time_1 is not None and time_2 is not None and time_3 is not None and time_4 is not None
				):
					offset_temp, one_way_delay = calculate_time_values(time_1, time_2, time_3, time_4, print_messages=print_ptp_messages)
					if one_way_delay > 3000:
						offsetList.append(offsetCount)
						offsetCount = 0
						if print_ptp_messages:
							print('Skipped offset change!!!!')
					else:
						offsetCount += 1
						offset = offset_temp
						if print_ptp_messages:
							print(offsetList)

					master_clock_time = time.ticks_us() - offset
					if print_ptp_messages:
						print('master_clock_time', int(master_clock_time))
					sync_flag = False
					follow_up_flag = False
					delay_response_flag = False

			if check_socket_count > 1100:
				check_socket_count = 0
				try:
					# Send the whole string
					ptp_sock.sendall('CHECK_CONNECTED')
					if print_ptp_messages:
						print('\nSent', time.ticks_us() / 1000, 'ms:', 'CHECK_CONNECTED')

				except OSError as err:
					if err.errno == 104:  # ECONNRESET
						print("send_button_events OS error ECONNRESET:", err)
					else:
						print("send_button_events OS error:", err)

					ptp_sock.close()
					PtpSocketConnectedFlag = False
			else:
				check_socket_count += 1

			time.sleep_ms(1)

		machine.idle()


# Initialize ---------------------------------------------------

# Constants
HOST = '192.168.8.1'
PORT = 60032
PTP_PORT = 60042
SSID = 'ScoreNet'
AUTH = (WLAN.WPA2, 'centari008')

# Variables -------------------------------------------------------------

message = None
rssi = None
vbatt = None
rssiThreadRunning = False
sendBlocksFlag = False
need_acknowledgement_flag = False
block_presses_flag = False
led_dict_values = []
acknowledgement_count = 0
startRssiForSendBlocksThreadFlag = True
rssiSentForSendBlocks = False
startRssiThreadFlag = True
startPtpFlag = False
ptp_thread_flag = False
PtpSocketCreatedFlag = False
PtpSocketConnectedFlag = False
PtpSocketCreatedCount = 0
ptp_sock = None
block_data = ''
battery_strength_display = False
battery_strength_display_count = 0
signal_strength_thread_flag = False
signal_strength_display = False
signal_strength_display_count = 0
SearchTimeoutDuration = 60
BatteryTimeoutDuration = 3
LongPressTimeoutDuration = 2.5
ConnectedDarkTimeoutDuration = 10
ConnectedPowerDownTimeoutDuration = 760
MainLoopFrequencyMs = 50
buttonThreadFrequency = 5
darkFlag = False
PowerOffSequenceFlag = True
PowerOnSequenceFlag = True
SearchBatteryTestModeFlag = False
ReceiverDiscoveredFlag = False
TransferFilesFlag = False
TransferFilesCompleteFlag = False
SocketConnectedFlag = False
socketCreatedFlag = False
socketCreatedCount = 0
offset = 0
mode = 'SearchModes'
led_sequence = LedSequences(LedDict)
printFlag = True

timePin = Pin('P22', mode=Pin.OUT)
timePin.value(False)

# Turn all off
led_sequence.all_off()

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

# Write tree.json file
with open('tree.json', 'w') as f:
	json_string = json.dumps(JsonTreeDict)
	f.write(json_string)
# print('\njson_string', json_string)

# Timers
search_mode_timer = Timer.Chrono()
battery_mode_timer = Timer.Chrono()
long_press_timer = Timer.Chrono()
connected_mode_power_down_timer = Timer.Chrono()

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
	Pin('P12', mode=Pin.OUT)(True)
	wlan.antenna(WLAN.EXT_ANT)

_thread.start_new_thread(ptp_thread, [])
_thread.start_new_thread(handle_button_event_thread, [])


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
		led_sequence.battery_test(enable=SearchBatteryTestModeFlag, on_off=True)

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
			led_sequence.battery_test(enable=SearchBatteryTestModeFlag, on_off=False)
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

				if not socketCreatedFlag:
					# Create and connect a socket
					try:
						# Create an AF_INET, STREAM socket (TCP)
						sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
						print('Socket Created', time.ticks_us()/1000, 'ms:')
						socketCreatedFlag = True
						SearchBatteryTestModeFlag = False
						led_sequence.timer.start()
						search_mode_timer.start()

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
					print('Failed to connect to ' + HOST, ': socketCreatedCount', socketCreatedCount)
					socketCreatedCount += 1
					if socketCreatedCount > 50:
						socketCreatedCount = 0
						socketCreatedFlag = False
						print('Kick New Socket Creation', time.ticks_us()/1000, 'ms:')

			if SocketConnectedFlag:
				SocketConnectedFlag = False
				PtpSocketCreatedFlag = False
				PtpSocketConnectedFlag = False

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

				# Rebuild fresh json tree
				led_sequence.all_off()
				JsonTreeDict = build_json_tree(LedDict, ButtDict, LedInfoDict, ButtonInfoDict)

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
				connected_mode_power_down_timer.stop()
				connected_mode_power_down_timer.reset()
				connected_mode_power_down_timer.start()
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
			connected_mode_power_down_timer.stop()
			connected_mode_power_down_timer.reset()
			connected_mode_power_down_timer.start()

	elif mode == 'ConnectedMode':
		# print('\nConnectedMode')
		# print('\nnConnectedMode start', time.ticks_us() / 1000, 'ms:')
		'''

		# Search Mode Timer Check
		if connected_mode_power_down_timer.read() > ConnectedPowerDownTimeoutDuration:
			print('\nconnected_mode_power_down_timer triggered at ', connected_mode_power_down_timer.read(), 's.')
			connected_mode_power_down_timer.stop()
			connected_mode_power_down_timer.reset()
			# ENTER Sleep Mode
			print('ENTER deep sleep\n')
			ptp_sock.close()
			machine.deepsleep()
		elif (
				connected_mode_power_down_timer.read() > ConnectedDarkTimeoutDuration
				and not darkFlag and not JsonTreeDict['command_flags']['get_rssi']
				and not JsonTreeDict['command_flags']['send_blocks']):
			print('\nconnected_mode_dark_timer triggered at ', connected_mode_power_down_timer.read(), 's.')
			led_sequence.all_off()
			darkFlag = True

		# Handle button events
		JsonTreeDict, event_flag = handle_button_event(JsonTreeDict, ButtEventDict, offset)

		# Send button events to server
		if event_flag:
			connected_mode_power_down_timer.stop()
			connected_mode_power_down_timer.reset()
			connected_mode_power_down_timer.start()
			darkFlag = False
			json_tree_fragment_dict = build_json_tree_fragment_dict(JsonTreeDict)
			sock, mode = send_events(sock, json_tree_fragment_dict, mode)
		'''

		# Check for data
		sock, data, mode, socketCreatedFlag = check_receive(sock, mode, socketCreatedFlag, print_flag=printFlag)

		if data:
			# Format data
			tic = time.ticks_us() / 1000
			if printFlag:
				print('Data START', tic, 'ms')

			if block_presses_flag:
				block_presses_flag = False
				led_sequence.set_led_dict_values(led_dict_values)

			need_acknowledgement_flag = False
			acknowledgement_count = 0

			index_list = find_substrings(data, 'JSON_FRAGMENT', print_flag=printFlag)
			fragment_list = slice_fragments(data, index_list)
			for fragment_index, fragment in enumerate(fragment_list):
				fragment_list[fragment_index] = convert_to_json_format(fragment)

			# Process data
			for fragment in fragment_list:
				if not battery_strength_display and not signal_strength_thread_flag and not signal_strength_display:
					check_led_data(fragment, LedDict, print_flag=False)
				check_get_rssi_flag(fragment, JsonTreeDict, print_flag=False)
				check_send_blocks_flag(fragment, JsonTreeDict, print_flag=False)
				check_power_down_flag(fragment, JsonTreeDict, print_flag=False)
				check_signal_strength_display_flag(fragment, JsonTreeDict, print_flag=False)
				check_battery_strength_display_flag(fragment, JsonTreeDict, print_flag=False)
			toc = time.ticks_us() / 1000
			if printFlag:
				print('\nData Processed', toc, 'ms, Dif Proc', toc - tic, 'ms')
		else:
			if need_acknowledgement_flag:
				if acknowledgement_count >= 3 and not block_presses_flag:
					acknowledgement_count = 0
					need_acknowledgement_flag = False
					block_presses_flag = True
					print('\nNo ACK received', time.ticks_us() / 1000, 'ms')
					led_dict_values = led_sequence.get_led_dict_values()
					led_sequence.all_on()
				else:
					acknowledgement_count += 1

		# React to get_rssi
		if JsonTreeDict['command_flags']['get_rssi'] and not block_presses_flag:
			if startRssiThreadFlag:
				startRssiThreadFlag = False
				rssiThreadRunning = True
				_thread.start_new_thread(get_rssi_thread, [wlan])
				print('after thread start', time.ticks_us() / 1000, 'ms: rssi =', rssi)

			if not rssiThreadRunning and rssi is not None:
				json_tree_fragment_dict = build_rssi_fragment_dict(rssi)
				need_acknowledgement_flag, sock, mode = send_events(sock, json_tree_fragment_dict, mode)
				print('rssi sent', time.ticks_us() / 1000, 'ms')
				startRssiThreadFlag = True

		# React to send_blocks
		send_blocks = JsonTreeDict['command_flags']['send_blocks']
		if send_blocks:
			if startRssiForSendBlocksThreadFlag:
				startRssiForSendBlocksThreadFlag = False
				rssiThreadRunning = True
				sendBlocksFlag = True
				_thread.start_new_thread(get_rssi_thread, [wlan])
				print('after thread start', time.ticks_ms(), 'rssi =', rssi)

			if not rssiThreadRunning and rssi is not None and not rssiSentForSendBlocks:
				rssiSentForSendBlocks = True
				json_tree_fragment_dict = build_rssi_fragment_dict(rssi)
				need_acknowledgement_flag, sock, mode = send_events(sock, json_tree_fragment_dict, mode)
				print('rssi sent', time.ticks_ms())
				print('Start send_blocks')
				_thread.start_new_thread(send_blocks_thread, [])
				print('after thread start', time.ticks_ms())

			if not startRssiForSendBlocksThreadFlag and rssiSentForSendBlocks and not sendBlocksFlag:
				JsonTreeDict['command_flags']['send_blocks'] = False
				print('Test 2 Done in main loop')
				ButtEventDict['P23'] = 3  # Pretend mode was pressed up to trigger close on RD
				connected_mode_power_down_timer.stop()
				connected_mode_power_down_timer.reset()
				connected_mode_power_down_timer.start()
		else:
			startRssiForSendBlocksThreadFlag = True
			rssiSentForSendBlocks = False
			sendBlocksFlag = False

		# React to power_down event
		if JsonTreeDict['command_flags']['power_down']:
			print('\n======== END Connected Modes ========\n')
			print('\n======== BEGIN Power Off Sequence Mode ========\n')
			mode = 'PoweringDownMode'
			led_sequence.timer.stop()
			led_sequence.timer.reset()
			led_sequence.timer.start()

		# React to signal_strength_display event
		if JsonTreeDict['command_flags']['signal_strength_display']:
			JsonTreeDict['command_flags']['signal_strength_display'] = False
			print('\nsignal_strength_display activated')
			signal_strength_thread_flag = True
			LedDict['P10'].value(True)
			LedDict['P11'].value(True)
			rssiThreadRunning = True
			_thread.start_new_thread(get_rssi_thread, [wlan])
			print('after thread start', time.ticks_ms(), 'rssi =', rssi)

		# React to signal_strength_thread ending
		if signal_strength_thread_flag and not JsonTreeDict['command_flags']['battery_strength_display'] and not battery_strength_display:
			if not rssiThreadRunning:
				signal_strength_thread_flag = False
				signal_strength_display = True
				if rssi is not None:
					led_sequence.signal_test(enable=True, on_off=signal_strength_display, rssi=rssi)
				print('\nsignal_strength_display start', time.ticks_us() / 1000, 'ms')

		# React to signal_strength_display timing out
		if signal_strength_display and not JsonTreeDict['command_flags']['battery_strength_display'] and not battery_strength_display:
			if signal_strength_display_count >= 50:  # Measured once to take 2.922s
				signal_strength_display_count = 0
				signal_strength_display = False
				led_sequence.signal_test(enable=True, on_off=signal_strength_display, rssi=rssi)
				print('\nsignal_strength_display stop', time.ticks_us() / 1000, 'ms')
			else:
				signal_strength_display_count += 1

		# React to battery_strength_display event
		if JsonTreeDict['command_flags']['battery_strength_display']:
			JsonTreeDict['command_flags']['battery_strength_display'] = False
			print('\nbattery_strength_display activated')
			signal_strength_thread_flag = False
			signal_strength_display = False
			battery_strength_display = True
			led_sequence.battery_test(enable=True, on_off=battery_strength_display)
			print('\nbattery_strength_display start', time.ticks_us() / 1000, 'ms')

		# React to battery_strength_display timing out
		if battery_strength_display:
			if battery_strength_display_count >= 50:  # Measured once to take 2.922s
				battery_strength_display_count = 0
				battery_strength_display = False
				led_sequence.battery_test(enable=True, on_off=battery_strength_display)
				print('\nbattery_strength_display stop', time.ticks_us() / 1000, 'ms')
			else:
				battery_strength_display_count += 1

		# React to Connected
		if ptp_thread_flag and not PtpSocketConnectedFlag:
			# Create and connect a socket
			if not PtpSocketCreatedFlag:
				try:
					# Create an AF_INET, STREAM socket (TCP)
					ptp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					print('PTP Socket Created', time.ticks_us() / 1000, 'ms')
					PtpSocketCreatedFlag = True

				except OSError as err:
					print("create_socket OS error:", err)
					print('Failed to create socket.')
			else:
				try:
					ptp_sock.connect((HOST, PTP_PORT))
					ptp_sock.setblocking(0)
					print('PTP Socket Connected to ' + HOST + ' on port ' + str(PTP_PORT))
					PtpSocketConnectedFlag = True

				except OSError as err:
					print("connect_socket OS error:", err)
					print('Failed to connect to ' + HOST, ': PtpSocketCreatedCount', PtpSocketCreatedCount)
					PtpSocketCreatedCount += 1
					if PtpSocketCreatedCount > 50:
						PtpSocketCreatedCount = 0
						PtpSocketCreatedFlag = False
						print('Kick New PTP Socket Creation', time.ticks_us() / 1000, 'ms')

		# Check connection to wifi and reconnect
		if not wlan.isconnected() and not JsonTreeDict['command_flags']['power_down']:
			mode = 'SearchModes'
			print('!!!!!!!!!!not wlan.isconnected()!!!!!!!!!!!')

			long_press_timer.stop()
			long_press_timer.reset()
			search_mode_timer.stop()
			search_mode_timer.reset()
			battery_mode_timer.stop()
			battery_mode_timer.reset()
			led_sequence.timer.stop()
			led_sequence.timer.reset()

			search_mode_timer.start()
			led_sequence.timer.start()

			print('\n======== END Connected Modes ========\n')
			print('\n======== BEGIN Search Modes ========\n')

		# print('\nConnectedMode END', time.ticks_us() / 1000, 'ms:')

	elif mode == 'PoweringDownMode':
		PowerOffSequenceFlag = led_sequence.power_off(PowerOffSequenceFlag)

		if not PowerOffSequenceFlag:
			mode = 'SleepMode'
			print('\n======== END Powering Down Mode ========\n')
			print('\n======== BEGIN Sleep Mode ========\n')

	elif mode == 'SleepMode':
		print('ENTER deep sleep\n')
		try:
			ptp_sock.close()
		except:
			pass
		machine.deepsleep()
	else:
		print('ERROR - no mode selected area should never be entered')
