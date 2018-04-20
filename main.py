# main.py -- put your code here!

import micropython
from machine import Pin
import socket, sys, json, select
#micropython.alloc_emergency_exception_buf(100)

#Functions
def decodeBytes(data):
	string=''
	for x,y in enumerate(data):
		z=chr(data[x])
		string=string + z
	return string

def buttonPress(pin):
	global buttStart, pressStart, currentPin, edge, PinDict, LedDict
	if not edge:
		buttStart=time.ticks_us()
		pressStart=time.ticks_ms()
		edge=1
		currentPin=PinDict[pin.id()]
		time.sleep_ms(20)
		LedDict['GP24'].toggle()
		LedDict['GP0'].toggle()
		LedDict['GP31'].toggle()
		LedDict['GP30'].toggle()
		LedDict['GP6'].toggle()
		LedDict['GP7'].toggle()
		LedDict['GP16'].toggle()

def buttonRelease(pin):
	global buttStart, currentPin, edge, PinDict, LedDict
	if not edge:
		edge=2
		buttStart=time.ticks_us()
		currentPin=PinDict[pin.id()]
		time.sleep_ms(20)
		LedDict['GP24'].toggle()
		LedDict['GP0'].toggle()
		LedDict['GP31'].toggle()
		LedDict['GP30'].toggle()
		LedDict['GP6'].toggle()
		LedDict['GP7'].toggle()
		LedDict['GP16'].toggle()

def handleButtonEvent():
	global buttStart, pressStart, currentPin, edge, PinDictReverse, buttonHeldFlag, longPressFlag, message, KeyDict
	if edge==1:
		machine.disable_irq()
		edge=0
		buttonHeldFlag=True
		currentPin=PinDictReverse[currentPin]
		machine.enable_irq()
		print (currentPin)
		buttTime=time.ticks_diff(buttStart, time.ticks_us())
		#print('PRESSED DOWN', buttTime, 'us  STATE', ButtDict[currentPin].value())
		#print()
		if not ButtDict[currentPin].value():
			ButtDict[currentPin].irq(trigger=Pin.IRQ_RISING, handler=buttonRelease)
	elif edge==2:
		machine.disable_irq()
		edge=0
		currentPin=PinDictReverse[currentPin]
		machine.enable_irq()
		buttTime=time.ticks_diff(buttStart, time.ticks_us())
		pressTime=time.ticks_diff(pressStart, time.ticks_ms())
		#print('		RELEASED', buttTime, 'us  STATE', ButtDict[currentPin].value())
		print('		PRESS TIME', pressTime, 'ms ')
		print()
		buttonHeldFlag=False
		ButtDict[currentPin].irq(trigger=Pin.IRQ_FALLING, handler=buttonPress)
		message = KeyMapDict[currentPin]

	if time.ticks_diff(pressStart, time.ticks_ms())>2000 and buttonHeldFlag:
		if not longPressFlag:
			print('LONG PRESS FLAG at 2000ms')
		longPressFlag=True
	else:
		longPressFlag=False

def checkReceive(s, receiveStart):
	# Get the list sockets which are readable
	read_sockets, write_sockets, error_sockets = select.select([s] , [], [])#adds 20ms every 16 loops at time i checked, this is when s is ready to be read

	for sock in read_sockets:
		#incoming message from remote server
		if sock == s:
			data=0
			try:
				data = sock.recv(4096)
			except OSError as err:
				err=int("{0}".format(err))
				if err==11:
					#Don't care about error here. It is normal for .recv() if non-blocking to wait for device to be ready
					pass
				else:
					print("OS error: {0}".format(err))
					sys.exit()
			if data:
				data=decodeBytes(data)
				loopTime=time.ticks_diff(receiveStart, time.ticks_us())
				print (data, loopTime)
				return data

def sendButtonPress(message, s):
	if message:
		#Send some data to remote server
		#Connect to remote server
		try :
			#Set the whole string
			s.sendall(message+'\n')
			print('Sent', message)
			#data = s.recv(1024)
			#print(data)
		except OSError as err:
			print("OS error: {0}".format(err))
			sys.exit();
		message=0
	return message


edge=0
message=0
buttonHeldFlag=False
longPressFlag=False
pressStart=time.ticks_ms()

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
LedDict['GP24']=Pin('GP24', mode=Pin.OUT, drive=Pin.LOW_POWER)#PIN_1=LED_5=topLed=PWM_1[5]
LedDict['GP0']=Pin('GP0', mode=Pin.OUT, drive=Pin.LOW_POWER)#PIN_13=LED_6=signalLed
LedDict['GP31']=Pin('GP31', mode=Pin.OUT, drive=Pin.LOW_POWER)#PIN_14=LED_4=strengthLedTop
LedDict['GP30']=Pin('GP30', mode=Pin.OUT, drive=Pin.LOW_POWER)#PIN_15=LED_3=strengthLedMiddleTop
LedDict['GP6']=Pin('GP6', mode=Pin.OUT, drive=Pin.LOW_POWER)#PIN_16=LED_2=strengthLedMiddleBottom
LedDict['GP7']=Pin('GP7', mode=Pin.OUT, drive=Pin.LOW_POWER)#PIN_17=LED_1=strengthLedBottom
LedDict['GP16']=Pin('GP16', mode=Pin.OUT, drive=Pin.LOW_POWER)#PIN_18=LED_7=batteryLed
#import wipy
#wipy.heartbeat(False)
#LedDict['GP25']=Pin('GP25', mode=Pin.OUT)#WiPy Heartbeat pin
LedPinList=list(LedDict.keys())
#print(LedPinList)

#Turn all off
for x in LedPinList:
	LedDict[x].value(False)

ButtDict={}
ButtDict['GP4']=Pin('GP4', mode=Pin.IN, pull=Pin.PULL_UP)#PIN_19=BUTT_0=KEY_10=modeButt
ButtDict['GP22']=Pin('GP22', mode=Pin.IN, pull=Pin.PULL_UP)#PIN_4=BUTT_1=KEY_9=outPlusButt=CX_DETECT
ButtDict['GP17']=Pin('GP17', mode=Pin.IN, pull=Pin.PULL_UP)#PIN_5=BUTT_2=KEY_8=strikePlusButt==LED2_IN
ButtDict['GP15']=Pin('GP15', mode=Pin.IN, pull=Pin.PULL_UP)#PIN_6=BUTT_3=KEY_7=ballPlusButt=PIC_RX2/LED1_IN
ButtDict['GP14']=Pin('GP14', mode=Pin.IN, pull=Pin.PULL_UP)#PIN_7=BUTT_4=KEY_6=homeMinusButt=RUN
ButtDict['GP13']=Pin('GP13', mode=Pin.IN, pull=Pin.PULL_UP)#PIN_8=BUTT_5=KEY_5=inningPlusButt=STOP
ButtDict['GP12']=Pin('GP12', mode=Pin.IN, pull=Pin.PULL_UP)#PIN_9=BUTT_6=KEY_4=guestMinusButt=RUN/STOP CLOCK
ButtDict['GP8']=Pin('GP8', mode=Pin.IN, pull=Pin.PULL_UP)#PIN_10=BUTT_7=KEY_3=homePlusButt=RUN/STOP DGT
ButtDict['GP11']=Pin('GP11', mode=Pin.IN, pull=Pin.PULL_UP)#PIN_11=BUTT_8=KEY_2=clockToggleButt=RESET 2
ButtDict['GP23']=Pin('GP23', mode=Pin.IN, pull=Pin.PULL_UP)#PIN_12=BUTT_9=KEY_1=guestPlusButt=RESET 1
ButtPinList=list(ButtDict.keys())
#print(ButtPinList)

#Pin dictionary and its reverse used to get pin id string out of callback
PinDict={}
PinList=[]
PinList.extend(LedPinList)
PinList.extend(ButtPinList)
#print (PinList)
PinRange=range(len(PinList))
for x, y in enumerate(PinList):
	PinDict[y]=PinRange[x]
#print(PinDict)
PinDictReverse={}
for x, y in enumerate(PinRange):
	PinDictReverse[y]=PinList[x]
#print(PinDictReverse)

#Translation dictionary for key names, correct this if pins ever change
KeyDict={'GP4':'KEY_10', 'GP22':'KEY_9', 'GP17':'KEY_8', 'GP11':'KEY_7', \
'GP14':'KEY_6', 'GP13':'KEY_5', 'GP12':'KEY_4', 'GP8':'KEY_3', \
'GP15':'KEY_2', 'GP23':'KEY_1'}

#Translation dictionary for key names, correct this if pins ever change
KeyMapDict={'GP4':'E7', 'GP22':'D6', 'GP17':'D7', 'GP11':'B7', \
'GP14':'C6', 'GP13':'C7', 'GP12':'C8', 'GP8':'B6', \
'GP15':'D8', 'GP23':'B8'}

#Button Interrupts
for x in ButtPinList:
	ButtDict[x].irq(trigger=Pin.IRQ_FALLING, handler=buttonPress)

try:
	#create an AF_INET, STREAM socket (TCP)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except OSError as err:
	print("OS error: {0}".format(err))
	print ('Failed to create socket.')
	sys.exit();

print ('Socket Created')

host='192.168.1.100'
port=60032

try:
	s.connect((host , port))
	s.setblocking(0)
except OSError as err:
	print("OS error: {0}".format(err))
	print ('Failed to connect to ' + host)
	sys.exit();

print ('Socket Connected to ' + host + ' on port ' + str(port))
#poller=select.poll()
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
	message=sendButtonPress(message, s)

	#Check for data
	data=checkReceive(s,receiveStart)

	#Check effect of received data



	'''
	loopTime=time.ticks_diff(loopStart, time.ticks_us())
	if loopTime>7000:
		print(loopTime,'us , with ', count,'loops in between')
		count=0
	count+=1
	'''
	wait=1
