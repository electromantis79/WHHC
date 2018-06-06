# main.py -- put your code here!

import micropython
import machine
import sys
import time
import pycom

from machine import Pin
from utils import *


# Constants
HOST = '192.168.8.1'
PORT = 60032


def button_event(pin):  # Pin Callback
	global ButtEventDict
	if pin.id() in ButtEventDict:
		last_state = ButtEventDict[pin.id()]
		# Down press = 1, Up press = 2
		#print('---------------------------', pin.id(), pin())
		#print('ButtEventDict[pin.id()]', last_state)
		if last_state == 0 and pin() == 0:
			last_state = 1
		elif last_state == 2 and pin() == 1:
			last_state = 3

		ButtEventDict[pin.id()] = last_state
		#print('ButtEventDict[pin.id()]', last_state)


# Variables -------------------------------------------------------------

message = None
rssi = None

# 10-Button Baseball Keypad
LedDict = {}
LedDict['P13'] = Pin(Pin.exp_board.G5, mode=Pin.OUT)  # PIN_1  = LED_5 = topLed = PWM_1[5]
LedDict['P18'] = Pin(Pin.exp_board.G30, mode=Pin.OUT)  # PIN_13 = LED_6 = signalLed
LedDict['P17'] = Pin(Pin.exp_board.G31, mode=Pin.OUT)  # PIN_14 = LED_4 = strengthLedTop
# LedDict['P16'] = Pin(Pin.exp_board.G3, mode=Pin.OUT)  # PIN_15 = LED_3 = strengthLedMiddleTop
LedDict['P15'] = Pin(Pin.exp_board.G0, mode=Pin.OUT)   # PIN_16 = LED_2 = strengthLedMiddleBottom
LedDict['P14'] = Pin(Pin.exp_board.G4, mode=Pin.OUT)   # PIN_17 = LED_1 = strengthLedBottom
LedDict['P19'] = Pin(Pin.exp_board.G6, mode=Pin.OUT)  # PIN_18 = LED_7 = batteryLed

#LedDict['P2'] = Pin(Pin.module.P2, mode = Pin.OUT)#WiPy Heartbeat pin
LedPinList = list(LedDict.keys())
print('\nLedDict', LedDict)

# Turn all off
for x in LedPinList:
	LedDict[x].value(False)

ButtDict = {}
ButtDict['P23'] = Pin(Pin.exp_board.G10, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_19 = BUTT_0 = KEY_10 = modeButt
ButtDict['P11'] = Pin(Pin.exp_board.G22, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_4 = BUTT_1 = KEY_9 = outPlusButt = CX_DETECT
ButtDict['P10'] = Pin(Pin.exp_board.G17, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_5 = BUTT_2 = KEY_8 = strikePlusButt =  = LED2_IN		BUTTON ON EXPANSION BOARD
ButtDict['P9'] = Pin(Pin.exp_board.G16, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_6 = BUTT_3 = KEY_7 = ballPlusButt = PIC_RX2/LED1_IN
ButtDict['P8'] = Pin(Pin.exp_board.G15, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_7 = BUTT_4 = KEY_6 = homeMinusButt = RUN
ButtDict['P7'] = Pin(Pin.exp_board.G14, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_8 = BUTT_5 = KEY_5 = inningPlusButt = STOP
ButtDict['P6'] = Pin(Pin.exp_board.G13, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_9 = BUTT_6 = KEY_4 = guestMinusButt = RUN/STOP CLOCK
ButtDict['P5'] = Pin(Pin.exp_board.G12, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_10 = BUTT_7 = KEY_3 = homePlusButt = RUN/STOP DGT
ButtDict['P4'] = Pin(Pin.exp_board.G11, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_11 = BUTT_8 = KEY_2 = clockToggleButt = RESET 2
ButtDict['P3'] = Pin(Pin.exp_board.G24, mode=Pin.IN, pull=Pin.PULL_UP)  # PIN_12 = BUTT_9 = KEY_1 = guestPlusButt = RESET 1
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

# Initialize ---------------------------------------------------

# Change LED from flashing blue default to solid red
pycom.heartbeat(False)
pycom.rgbled(0xff0000)

# Create and connect a socket
sock = connect_socket(HOST, PORT)

# Test voltage sense function
vbatt = get_battery_voltage(1)

rssi = get_rssi(wlan)

# MAIN LOOP
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
