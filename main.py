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
LongPressTimeoutDuration = 2.5
PowerOffSequenceFlag = False
PowerOnSequenceFlag = True

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
sleep_mode_timer = Timer.Chrono()
long_press_timer = Timer.Chrono()

# LED Power On Sequence
led_sequence.timer.start()
while PowerOnSequenceFlag:
	PowerOnSequenceFlag = led_sequence.power_on(PowerOnSequenceFlag)
	time.sleep_ms(50)

# END Boot Up Mode -----------------------

print('\n======== END Boot Up Mode ========')
print('\n======== BEGIN Search Mode ========\n')

# Search Mode ============================

# Clear any button presses
for button in ButtEventDict:
	ButtEventDict[button] = 0

# Wifi connection
if machine.reset_cause() != machine.SOFT_RESET:
	print('Initialising WLAN in station mode...', end=' ')
	wlan = WLAN(mode=WLAN.STA)
	wlan.ifconfig(config=('192.168.8.145', '255.255.255.0', '192.168.8.1', '8.8.8.8'))
	print('done.\nConnecting to WiFi network...', end='')
	wlan.connect(ssid=SSID, auth=AUTH)
	sleep_mode_timer.start()
	while 1 or not wlan.isconnected():
		machine.idle()
		#print('.', end='')

		# LED Sequences
		PowerOffSequenceFlag = led_sequence.power_off(PowerOffSequenceFlag)

		time.sleep_ms(50)

		# Sleep Mode Timer Check
		if sleep_mode_timer.read() > SearchTimeoutDuration:
			print('\nsleep_mode_timer triggered at ', sleep_mode_timer.read(), 's.')
			sleep_mode_timer.stop()
			sleep_mode_timer.reset()
			# ENTER Sleep Mode

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
						sleep_mode_timer.stop()
						sleep_mode_timer.reset()
						# ENTER Search Battery Test Mode
						print('\nENTER Search Battery Test Mode')
					else:
						# Any other button
						print('sleep_mode_timer', sleep_mode_timer.read(), 's.')
						sleep_mode_timer.reset()
						print('sleep_mode_timer after reset', sleep_mode_timer.read(), 's.')

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
					else:
						# Any other button
						print('sleep_mode_timer', sleep_mode_timer.read(), 's.')
						sleep_mode_timer.reset()
						print('sleep_mode_timer after reset', sleep_mode_timer.read(), 's.')

	print(' done.\n')

	ip, mask, gateway, dns = wlan.ifconfig()
	print('IP address: ', ip)
	print('Netmask:    ', mask)
	print('Gateway:    ', gateway)
	print('DNS:        ', dns)
	print()
else:
	# machine.SOFT_RESET

	wlan = WLAN()
	print('Wireless still connected =', wlan.isconnected(), '\n')
	if wlan.isconnected():
		ip, mask, gateway, dns = wlan.ifconfig()
		print('IP address: ', ip)
		print('Netmask:    ', mask)
		print('Gateway:    ', gateway)
		print('DNS:        ', dns)
		print()
	else:
		print('Connecting to WiFi network...', end='')
		wlan.connect(ssid=SSID, auth=AUTH)
		while not wlan.isconnected():
			machine.idle()
			time.sleep_ms(500)
			print('.', end='')

		ip, mask, gateway, dns = wlan.ifconfig()
		print(' done.\n')
		print('IP address: ', ip)
		print('Netmask:    ', mask)
		print('Gateway:    ', gateway)
		print('DNS:        ', dns)
		print()


# Create and connect a socket
sock = connect_socket(HOST, PORT)

# Test voltage sense function
vbatt = get_battery_voltage(1)

# Test rssi
rssi = get_rssi(wlan)

# Change LED from flashing blue default to solid red
pycom.heartbeat(False)
pycom.rgbled(0xff0000)

# Connected loop
count = 0
wait = 1
while wait:
	loopStart = time.ticks_us()
	machine.idle()

	# Send button press to server
	sock, message = send_button_press(sock, HOST, PORT, ButtEventDict, KeyMapDict)

	# Check for data
	sock, data = check_receive(sock, HOST, PORT)

	# Check effect of received data

	# Check connection to wifi and reconnect
	if not wlan.isconnected():
		print('\nLost wifi connection to ' + HOST)
		sys.exit()
		#wlan.connect(ssid=SSID, auth=AUTH)
		#sock.close()
		#while not wlan.isconnected():
		#	machine.idle()
		#sock=connect_socket()

	'''
	loopTime=time.ticks_diff(loopStart, time.ticks_us())
	if loopTime>7000:
		print(loopTime,'us , with ', count,'loops in between')
		count=0
	count+=1
	'''
	wait = 1
