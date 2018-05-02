# main.py -- put your code here!

import micropython, math
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
	global longPressStart, receiveStart, pressStart, currentPin, edge, PinDict, LedDict
	#print (pin.id(), edge)
	if not edge:
		edge=1
		receiveStart=time.ticks_us()
		pressStart=time.ticks_ms()
		longPressStart=time.ticks_ms()
		currentPin=PinDict[pin.id()]
		#print (pin.id(), edge)

		#time.sleep_ms(50)
		#LedDict['P19'].toggle()#PIN_1 =LED_5=topLed=PWM_1[5]
		LedDict['P18'].toggle()#PIN_13=LED_6=signalLed
		LedDict['P17'].toggle()#PIN_14=LED_4=strengthLedTop
		#LedDict['P16'].toggle()#PIN_15=LED_3=strengthLedMiddleTop
		LedDict['P15'].toggle()#PIN_16=LED_2=strengthLedMiddleBottom
		LedDict['P14'].toggle()#PIN_17=LED_1=strengthLedBottom
		#LedDict['P13'].toggle()#PIN_18=LED_7=batteryLed		LED ON EXPANSION BOARD

def buttonRelease(pin):
	global currentPin, edge, PinDict, LedDict
	if not edge:
		edge=2
		currentPin=PinDict[pin.id()]
		#time.sleep_ms(20)
		#LedDict['P19'].toggle()#PIN_1 =LED_5=topLed=PWM_1[5]
		LedDict['P18'].toggle()#PIN_13=LED_6=signalLed
		LedDict['P17'].toggle()#PIN_14=LED_4=strengthLedTop
		#LedDict['P16'].toggle()#PIN_15=LED_3=strengthLedMiddleTop
		LedDict['P15'].toggle()#PIN_16=LED_2=strengthLedMiddleBottom
		LedDict['P14'].toggle()#PIN_17=LED_1=strengthLedBottom
		#LedDict['P13'].toggle()#PIN_18=LED_7=batteryLed		LED ON EXPANSION BOARD

def handleButtonEvent():
	global longPressStart, pressStart, currentPin, edge, PinDictReverse, buttonHeldFlag, longPressFlag, message, KeyDict, rssi, buttonPressFlag
	if edge==1:
		machine.disable_irq()
		edge=0
		buttonHeldFlag=True
		currentPin=PinDictReverse[currentPin]
		print (currentPin)
		message = KeyMapDict[currentPin]
		buttonPressFlag=True
		if not ButtDict[currentPin].value():
			ButtDict[currentPin].callback(trigger=Pin.IRQ_RISING, handler=buttonRelease)
		machine.enable_irq()
	elif edge==2:
		machine.disable_irq()
		edge=0
		currentPin=PinDictReverse[currentPin]
		pressTime=time.ticks_diff(pressStart, time.ticks_ms())
		print('		PRESS TIME', pressTime, 'ms ')
		print()
		buttonHeldFlag=False
		ButtDict[currentPin].callback(trigger=Pin.IRQ_FALLING, handler=buttonPress)
		machine.enable_irq()

	if time.ticks_diff(longPressStart, time.ticks_ms())>2000 and buttonHeldFlag:
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

def checkReceive():
	global s, HOST, PORT, receiveStart
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
		buttTime=time.ticks_diff(receiveStart, time.ticks_us())
		print ('Data Received', data, 'round trip Time', buttTime, 'us')
		return data

def sendButtonPress():
	global rssi, s, HOST, PORT, message, lastMessage, resendFlag, buttonPressFlag
	if rssi is not None:
		message=rssi
		rssi=None
		buttonPressFlag=True
	if resendFlag:
		resendFlag=False
		message='@'
		utime.sleep_ms(500)
	if message:
		#Send some data to remote server
		#Connect to remote server
		lastMessage=message
		try :
			#Send the whole string
			s.sendall(message)
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

def getBatteryVoltage(show=0):
	'''
	typedef enum {
		ADC_ATTEN_0DB = 0,
		ADC_ATTEN_3DB, // 1
		ADC_ATTEN_6DB, // 2
		ADC_ATTEN_12DB, // 3
		ADC_ATTEN_MAX, // 4
	} adc_atten_t;
	'''
	adc = machine.ADC(0)
	adcread = adc.channel(attn=2, pin='P16')
	samplesADC = [0.0]*numADCreadings; meanADC = 0.0
	i = 0
	while (i < numADCreadings):
		adcint = adcread()
		samplesADC[i] = adcint
		meanADC += adcint
		i += 1
	meanADC /= numADCreadings
	varianceADC = 0.0
	for adcint in samplesADC:
		varianceADC += (adcint - meanADC)**2
	varianceADC /= (numADCreadings - 1)
	vbatt=((meanADC/3)*1400/1024)*171/(56*1000)# Vbatt=Vmeasure*((115+56)/56)
	if show:
		print("%u ADC readings :\n%s" %(numADCreadings, str(samplesADC)))
		print("Mean of ADC readings (0-4095) = %15.13f" % meanADC)
		print("Mean of ADC readings (0-1846 mV) = %15.13f" % ((meanADC)*1846/4096)) # Calabrated manually
		print("Variance of ADC readings = %15.13f" % varianceADC)
		print("Standard Deviation of ADC readings = %15.13f" % math.sqrt(varianceADC))
		print("10**6*Variance/(Mean**2) of ADC readings = %15.13f" % ((varianceADC*10**6)//(meanADC**2)))
		print("Battery voltage = %15.13f" % (vbatt))
	return vbatt

numADCreadings = const(100)
edge=0
message=0
lastMessage=0
buttonPressFlag=0
resendCounter=0
rssi=None
buttonHeldFlag=False
longPressFlag=False
resendFlag=False
receivedLastMessageFlag=False
pressStart=time.ticks_ms()
longPressStart=time.ticks_ms()
receiveStart=time.ticks_us()
HOST='192.168.8.1'
PORT=60032

# 10-Button Baseball Keypad-------------------------------------------

LedDict={}
LedDict['P13']=Pin(Pin.exp_board.G5, mode=Pin.OUT) #PIN_1 =LED_5=topLed=PWM_1[5]
LedDict['P18']=Pin(Pin.exp_board.G30, mode=Pin.OUT)   #PIN_13=LED_6=signalLed
LedDict['P17']=Pin(Pin.exp_board.G31, mode=Pin.OUT) #PIN_14=LED_4=strengthLedTop
#LedDict['P16']=Pin(Pin.exp_board.G3, mode=Pin.OUT) #PIN_15=LED_3=strengthLedMiddleTop
LedDict['P15']=Pin(Pin.exp_board.G0, mode=Pin.OUT)   #PIN_16=LED_2=strengthLedMiddleBottom
LedDict['P14']=Pin(Pin.exp_board.G4, mode=Pin.OUT)   #PIN_17=LED_1=strengthLedBottom
LedDict['P19']=Pin(Pin.exp_board.G6, mode=Pin.OUT) #PIN_18=LED_7=batteryLed
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
ButtDict['P11']=Pin(Pin.exp_board.G22, mode=Pin.IN, pull=Pin.PULL_UP)#PIN_4=BUTT_1=KEY_9=outPlusButt=CX_DETECT
ButtDict['P10']=Pin(Pin.exp_board.G17, mode=Pin.IN, pull=Pin.PULL_UP)#PIN_5=BUTT_2=KEY_8=strikePlusButt==LED2_IN		BUTTON ON EXPANSION BOARD
ButtDict['P9']=Pin(Pin.exp_board.G16, mode=Pin.IN, pull=Pin.PULL_UP)#PIN_6=BUTT_3=KEY_7=ballPlusButt=PIC_RX2/LED1_IN
ButtDict['P8']=Pin(Pin.exp_board.G15, mode=Pin.IN, pull=Pin.PULL_UP)#PIN_7=BUTT_4=KEY_6=homeMinusButt=RUN
ButtDict['P7']=Pin(Pin.exp_board.G14, mode=Pin.IN, pull=Pin.PULL_UP)#PIN_8=BUTT_5=KEY_5=inningPlusButt=STOP
ButtDict['P6']=Pin(Pin.exp_board.G13, mode=Pin.IN, pull=Pin.PULL_UP)#PIN_9=BUTT_6=KEY_4=guestMinusButt=RUN/STOP CLOCK
ButtDict['P5']=Pin(Pin.exp_board.G12, mode=Pin.IN, pull=Pin.PULL_UP)#PIN_10=BUTT_7=KEY_3=homePlusButt=RUN/STOP DGT
ButtDict['P4']=Pin(Pin.exp_board.G11, mode=Pin.IN, pull=Pin.PULL_UP)#PIN_11=BUTT_8=KEY_2=clockToggleButt=RESET 2
ButtDict['P3']=Pin(Pin.exp_board.G24, mode=Pin.IN, pull=Pin.PULL_UP)#PIN_12=BUTT_9=KEY_1=guestPlusButt=RESET 1
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
KeyDict={'P23':'KEY_10', 'P11':'KEY_9', 'P10':'KEY_8', 'P9':'KEY_7', \
'P8':'KEY_6', 'P7':'KEY_5', 'P6':'KEY_4', 'P5':'KEY_3', \
'P4':'KEY_2', 'P3':'KEY_1'}
print('\nKeyDict', KeyDict)

#Translation dictionary for key names, correct this if pins ever change
KeyMapDict={'P23':'E7', 'P11':'D6', 'P10':'D7', 'P9':'D8', \
'P8':'C6', 'P7':'C7', 'P6':'C8', 'P5':'B6', \
'P4':'B7', 'P3':'B8'}
print('\nKeyMapDict', KeyMapDict)

#Button Interrupts
for x in ButtPinList:
	ButtDict[x].callback(trigger=Pin.IRQ_FALLING, handler=buttonPress)

#Initalize

#Create and connect a socket
s=connectSocket(HOST, PORT)

vbatt=getBatteryVoltage(1)

#MAIN LOOP
count=0
wait=1
while wait:
	loopStart=time.ticks_us()
	machine.idle()

	#Generic button event function
	handleButtonEvent()

	#Send button press to server
	sendButtonPress()

	#Check for data
	data=checkReceive()

	#Check effect of received data
	if data:
		print('Process', data)
		if data[0]!='[':
			dataList=[]
			for x in range(len(data)):
				if x%2:
					dataList.append(data[x-1:x+1])
				if data[x]=='@':
					resendFlag=False
					receivedLastMessageFlag=False
					buttonPressFlag=False
					resendCounter=0
					print(data[x], 'Received')
			print('dataList', dataList)
			if dataList:
				for pair in dataList:
					print('pair', pair)
					if pair==lastMessage:
						print(pair,'acknowledged by server.')
						receivedLastMessageFlag=True
					else:
						if pair=='P1':
							LedDict['P19'](True)
						elif pair=='P0':
							LedDict['P19'](False)
						elif pair=='T1':
							pass
						elif pair=='T0':
							pass
						elif pair=='S1':
							pass
						elif pair=='S0':
							pass
						elif pair=='IB':
							pass
						elif pair=='IT':
							pass
						else:
							pass

	if buttonPressFlag:
		if not receivedLastMessageFlag:
			if resendCounter>100:
				resendFlag=True
				print('Resending Request for Status!')
			resendCounter+=1
		else:
			print('resendCounter canceled at', resendCounter)
			receivedLastMessageFlag=False
			buttonPressFlag=False
			resendCounter=0

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
