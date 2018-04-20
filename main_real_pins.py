# main.py -- put your code here!

import micropython
from machine import Pin
import socket, sys, json, select, utime

#Functions
def decodeBytes(data):
	string=''
	for x,y in enumerate(data):
		z=chr(data[x])
		string=string + z
	return string

def buttonPress(pin):
	global buttStart, pressStart, currentPin, edge, PinDict, LedDict
	#print (pin.id(), edge)
	if not edge:
		buttStart=time.ticks_us()
		pressStart=time.ticks_ms()
		edge=1
		currentPin=PinDict[pin.id()]
		#print (pin.id(), edge)

		time.sleep_ms(20)
		LedDict['P22'].toggle()#PIN_1 =LED_5=topLed=PWM_1[5]
		LedDict['P3'].toggle()#PIN_13=LED_6=signalLed
		LedDict['P4'].toggle()#PIN_14=LED_4=strengthLedTop
		LedDict['P8'].toggle()#PIN_15=LED_3=strengthLedMiddleTop
		LedDict['P9'].toggle()#PIN_16=LED_2=strengthLedMiddleBottom		LED ON EXPANSION BOARD
		LedDict['P10'].toggle()#PIN_17=LED_1=strengthLedBottom
		LedDict['P11'].toggle()#PIN_18=LED_7=batteryLed

def buttonRelease(pin):
	global buttStart, currentPin, edge, PinDict, LedDict
	if not edge:
		edge=2
		#buttStart=time.ticks_us()
		currentPin=PinDict[pin.id()]
		time.sleep_ms(20)
		LedDict['P22'].toggle()#PIN_1 =LED_5=topLed=PWM_1[5]
		LedDict['P3'].toggle()#PIN_13=LED_6=signalLed
		LedDict['P4'].toggle()#PIN_14=LED_4=strengthLedTop
		LedDict['P8'].toggle()#PIN_15=LED_3=strengthLedMiddleTop
		LedDict['P9'].toggle()#PIN_16=LED_2=strengthLedMiddleBottom		LED ON EXPANSION BOARD
		LedDict['P10'].toggle()#PIN_17=LED_1=strengthLedBottom
		LedDict['P11'].toggle()#PIN_18=LED_7=batteryLed

def handleButtonEvent():
	global buttStart, pressStart, currentPin, edge, PinDictReverse, buttonHeldFlag, longPressFlag, message, KeyDict, rssi
	if edge==1:
		machine.disable_irq()
		edge=0
		buttonHeldFlag=True
		currentPin=PinDictReverse[currentPin]
		machine.enable_irq()
		print (currentPin)
		#buttTime=time.ticks_diff(buttStart, time.ticks_us())
		#print('PRESSED DOWN', buttTime, 'us  STATE', ButtDict[currentPin].value())
		#print()
		if not ButtDict[currentPin].value():
			ButtDict[currentPin].callback(trigger=Pin.IRQ_RISING, handler=buttonRelease)
	elif edge==2:
		machine.disable_irq()
		edge=0
		currentPin=PinDictReverse[currentPin]
		machine.enable_irq()
		#buttTime=time.ticks_diff(buttStart, time.ticks_us())
		pressTime=time.ticks_diff(pressStart, time.ticks_ms())
		#print('		RELEASED', buttTime, 'us  STATE', ButtDict[currentPin].value())
		print('		PRESS TIME', pressTime, 'ms ')
		print()
		buttonHeldFlag=False
		ButtDict[currentPin].callback(trigger=Pin.IRQ_FALLING, handler=buttonPress)
		message = KeyMapDict[currentPin]

	if time.ticks_diff(pressStart, time.ticks_ms())>2000 and buttonHeldFlag:
		if not longPressFlag:
			print('LONG PRESS FLAG at 2000ms')
			rssi=getRssi(currentPin)
			#sys.exit()
		longPressFlag=True
	else:
		longPressFlag=False

def getRssi(currentPin):
	if currentPin=='P10':
		nets=wlan.scan()
		for net in nets:
			if net.ssid == 'ScoreNet':
				rssi=net.rssi
				rssi=str(rssi)[1:]
				print(rssi)
				return rssi

def checkReceive(receiveStart):
	global s, HOST, PORT, buttStart
	data=0
	try:
		data = s.recv(4096)
	except OSError as err:
		#print (err, err.errno)

		if err.errno==11:
			#Don't care about error here. It is normal for .recv() if non-blocking to wait for device to be ready
			print ('special 11 spot', err)
			pass
		elif err.errno==113:
			print("checkReceive OS error:", err)
			machine.reset()
		elif err.errno==104: #ECONNRESET
			print("checkReceive OS error:", err)
			utime.sleep_us(10)
			s=connectSocket(HOST, PORT)
		else:
			print("checkReceive OS error:", err)
			machine.reset()

	if data:
		data=decodeBytes(data)
		buttTime=time.ticks_diff(buttStart, time.ticks_us())
		print ('Data Received', data, 'round trip Time', buttTime, 'us')
		return data

def sendButtonPress(message):
	global rssi, s, HOST, PORT
	if rssi is not None:
		message=rssi
		rssi=None
	if message:
		#Send some data to remote server
		#Connect to remote server
		try :
			#Set the whole string
			s.sendall(message+'\n')
			print('Sent', message)
			#data = s.recv(1024)
			#print(data)
			message=0
		except OSError as err:
			if err.errno==104: #ECONNRESET
				print("sendButtonPress OS error:", err)
				utime.sleep_us(10)
				s=connectSocket(HOST, PORT)
			else:
				print("sendButtonPress OS error:", err)
				machine.reset()
	return message

def connectSocket(HOST, PORT):
	try:
		#create an AF_INET, STREAM socket (TCP)
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except OSError as err:
		print("connectSocket OS error:", err)
		print ('Failed to create socket.')
		machine.reset()

	print ('Socket Created')

	try:
		s.connect((HOST , PORT))
		s.setblocking(0)
	except OSError as err:
		print("connectSocket OS error:", err)
		print ('Failed to connect to ' + HOST)
		machine.reset()

	print ('Socket Connected to ' + HOST + ' on port ' + str(PORT))
	return s

edge=0
message=0
rssi=None
buttonHeldFlag=False
longPressFlag=False
pressStart=time.ticks_ms()
buttStart=0
HOST='192.168.10.100'
PORT=60032

'''
# Expansion board setup
PIN_18=LED_7=batteryLed=Pin('GP16', mode=Pin.OUT)
batteryLed.value(1)
PIN_5=BUTT_2=strikePlusButt=Pin('GP17', mode=Pin.IN, pull=Pin.PULL_UP)
#Interrupt
BUTT_2.irq(trigger=Pin.IRQ_FALLING, handler=buttonPress)
'''
# 10-Button Baseball Keypad-------------------------------------------

LedDict={}
LedDict['P22']=Pin(Pin.exp_board.G9, mode=Pin.OUT) #PIN_1 =LED_5=topLed=PWM_1[5]
LedDict['P3']=Pin(Pin.exp_board.G24, mode=Pin.OUT)   #PIN_13=LED_6=signalLed
LedDict['P4']=Pin(Pin.exp_board.G11, mode=Pin.OUT) #PIN_14=LED_4=strengthLedTop
LedDict['P8']=Pin(Pin.exp_board.G15, mode=Pin.OUT) #PIN_15=LED_3=strengthLedMiddleTop
LedDict['P9']=Pin(Pin.exp_board.G16, mode=Pin.OUT)   #PIN_16=LED_2=strengthLedMiddleBottom		LED ON EXPANSION BOARD
LedDict['P10']=Pin(Pin.exp_board.G17, mode=Pin.OUT)   #PIN_17=LED_1=strengthLedBottom
LedDict['P11']=Pin(Pin.exp_board.G22, mode=Pin.OUT) #PIN_18=LED_7=batteryLed
import pycom
pycom.heartbeat(False)
pycom.rgbled(0xff0000)
#LedDict['P2']=Pin(Pin.module.P2, mode=Pin.OUT)#WiPy Heartbeat pin
LedPinList=list(LedDict.keys())
print('\nLedDict', LedDict)

#Turn all off
for x in LedPinList:
	LedDict[x].value(False)

ButtDict={}
ButtDict['P23']=Pin(Pin.exp_board.G10, mode=Pin.IN, pull=Pin.PULL_UP)#PIN_19=BUTT_0=KEY_10=modeButt
ButtDict['P21']=Pin(Pin.exp_board.G8, mode=Pin.IN, pull=Pin.PULL_UP)#PIN_4=BUTT_1=KEY_9=outPlusButt=CX_DETECT
ButtDict['P20']=Pin(Pin.exp_board.G7, mode=Pin.IN, pull=Pin.PULL_UP)#PIN_5=BUTT_2=KEY_8=strikePlusButt==LED2_IN		BUTTON ON EXPANSION BOARD
ButtDict['P19']=Pin(Pin.exp_board.G6, mode=Pin.IN, pull=Pin.PULL_UP)#PIN_6=BUTT_3=KEY_7=ballPlusButt=PIC_RX2/LED1_IN
ButtDict['P18']=Pin(Pin.exp_board.G30, mode=Pin.IN, pull=Pin.PULL_UP)#PIN_7=BUTT_4=KEY_6=homeMinusButt=RUN
ButtDict['P17']=Pin(Pin.exp_board.G31, mode=Pin.IN, pull=Pin.PULL_UP)#PIN_8=BUTT_5=KEY_5=inningPlusButt=STOP
ButtDict['P16']=Pin(Pin.exp_board.G3, mode=Pin.IN, pull=Pin.PULL_UP)#PIN_9=BUTT_6=KEY_4=guestMinusButt=RUN/STOP CLOCK
ButtDict['P15']=Pin(Pin.exp_board.G0, mode=Pin.IN, pull=Pin.PULL_UP)#PIN_10=BUTT_7=KEY_3=homePlusButt=RUN/STOP DGT
ButtDict['P14']=Pin(Pin.exp_board.G4, mode=Pin.IN, pull=Pin.PULL_UP)#PIN_11=BUTT_8=KEY_2=clockToggleButt=RESET 2
ButtDict['P13']=Pin(Pin.exp_board.G5, mode=Pin.IN, pull=Pin.PULL_UP)#PIN_12=BUTT_9=KEY_1=guestPlusButt=RESET 1
ButtPinList=list(ButtDict.keys())
print('\nButtDict', ButtDict)

#Pin dictionary and its reverse used to get pin id string out of callback
PinDict={}
PinList=[]
PinList.extend(LedPinList)
PinList.extend(ButtPinList)
print ('\nPinList', PinList)
PinRange=range(len(PinList))
for x, y in enumerate(PinList):
	PinDict[y]=PinRange[x]
print('\nPinDict', PinDict)
PinDictReverse={}
for x, y in enumerate(PinRange):
	PinDictReverse[y]=PinList[x]
print('\nPinDictReverse', PinDictReverse)

#Translation dictionary for key names, correct this if pins ever change
KeyDict={'P23':'KEY_10', 'P21':'KEY_9', 'P20':'KEY_8', 'P19':'KEY_7', \
'P18':'KEY_6', 'P17':'KEY_5', 'P16':'KEY_4', 'P15':'KEY_3', \
'P14':'KEY_2', 'P13':'KEY_1'}
print('\nKeyDict', KeyDict)

#Translation dictionary for key names, correct this if pins ever change
KeyMapDict={'P23':'E7', 'P21':'D6', 'P20':'D7', 'P19':'D8', \
'P18':'C6', 'P17':'C7', 'P16':'C8', 'P15':'B6', \
'P14':'B7', 'P13':'B8'}
print('\nKeyMapDict', KeyMapDict)

#Button Interrupts
for x in ButtPinList:
	ButtDict[x].callback(trigger=Pin.IRQ_FALLING, handler=buttonPress)

#Initalize

#Create and connect a socket
s=connectSocket(HOST, PORT)


#MAIN LOOP
count=0
wait=1
while wait:
	receiveStart=time.ticks_us()
	loopStart=time.ticks_us()
	machine.idle()

	#Generic button event function
	handleButtonEvent()

	#Send button press to server
	message=sendButtonPress(message)

	#Check for data
	data=checkReceive(receiveStart)

	#Check effect of received data
	if data:
		print('Received', data)


	#Check connection to wifi and reconnect
	if not wlan.isconnected():
		print ('\nLost wifi connection to ' + HOST)
		sys.exit();
		#wlan.connect(ssid=SSID, auth=AUTH)
		#s.close()
		#while not wlan.isconnected():
		#	machine.idle()
		#s=connectSocket()

	'''
	loopTime=time.ticks_diff(loopStart, time.ticks_us())
	if loopTime>7000:
		print(loopTime,'us , with ', count,'loops in between')
		count=0
	count+=1
	'''
	wait=1
