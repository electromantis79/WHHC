# main.py -- put your code here!

import micropython
from machine import Pin
#micropython.alloc_emergency_exception_buf(100)

#Functions
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
	global buttStart, pressStart, currentPin, edge, PinDictReverse, buttonHeldFlag, longPressFlag
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
	if time.ticks_diff(pressStart, time.ticks_ms())>2000 and buttonHeldFlag:
		if not longPressFlag:
			print('LONG PRESS FLAG at 2000ms')
		longPressFlag=True
	else:
		longPressFlag=False

edge=0
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
ButtDict['GP11']=Pin('GP11', mode=Pin.IN, pull=Pin.PULL_UP)#PIN_6=BUTT_3=KEY_7=ballPlusButt=PIC_RX2/LED1_IN
ButtDict['GP14']=Pin('GP14', mode=Pin.IN, pull=Pin.PULL_UP)#PIN_7=BUTT_4=KEY_6=homeMinusButt=RUN
ButtDict['GP13']=Pin('GP13', mode=Pin.IN, pull=Pin.PULL_UP)#PIN_8=BUTT_5=KEY_5=inningPlusButt=STOP
ButtDict['GP12']=Pin('GP12', mode=Pin.IN, pull=Pin.PULL_UP)#PIN_9=BUTT_6=KEY_4=guestMinusButt=RUN/STOP CLOCK
ButtDict['GP8']=Pin('GP8', mode=Pin.IN, pull=Pin.PULL_UP)#PIN_10=BUTT_7=KEY_3=homePlusButt=RUN/STOP DGT
ButtDict['GP15']=Pin('GP15', mode=Pin.IN, pull=Pin.PULL_UP)#PIN_11=BUTT_8=KEY_2=clockToggleButt=RESET 2
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

#Button Interrupts
for x in ButtPinList:
	ButtDict[x].irq(trigger=Pin.IRQ_FALLING, handler=buttonPress)


#MAIN LOOP

wait=1
while wait:
	machine.idle()

	#Generic button event function
	handleButtonEvent()

	#Check effect of button release


