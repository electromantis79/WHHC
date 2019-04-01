from machine import Timer
from utils import *


class LedSequences(object):
	"""
	methods must be called from inside a loop to be called faster than or equal to the 50ms minimum

	LedDict['P20'] = Pin('P20', mode=Pin.OUT)  # PIN_2  = LED_5 = topLed = PWM_1[5]
	LedDict['P11'] = Pin('P11', mode=Pin.OUT)  # PIN_13 = LED_6 = signalLed
	LedDict['P10'] = Pin('P10', mode=Pin.OUT)  # PIN_14 = LED_4 = strengthLedTop = Strength Bar 4
	LedDict['P9'] = Pin('P9', mode=Pin.OUT)  # PIN_15 = LED_3 = strengthLedMiddleTop = Strength Bar 3
	LedDict['P8'] = Pin('P8', mode=Pin.OUT)   # PIN_16 = LED_2 = strengthLedMiddleBottom = Strength Bar 2
	LedDict['P7'] = Pin('P7', mode=Pin.OUT)   # PIN_17 = LED_1 = strengthLedBottom = Strength Bar 1
	LedDict['P6'] = Pin('P6', mode=Pin.OUT)  # PIN_18 = LED_7 = batteryLed
	"""

	def __init__(
			self, led_dict,
			batt_bar_threshold=(1.8, 2.4, 2.7, 3.0), signal_bar_threshold=(70, 60, 50, 40)):

		self.LedDict = led_dict
		self.timer = Timer.Chrono()
		self.transfer_cycle_flag = False
		self.printTimes = False
		self.battBarThresholdOne = batt_bar_threshold[0]
		self.battBarThresholdTwo = batt_bar_threshold[1]
		self.battBarThresholdThree = batt_bar_threshold[2]
		self.battBarThresholdFour = batt_bar_threshold[3]
		self.signalBarThresholdZero = signal_bar_threshold[0]
		self.signalBarThresholdOne = signal_bar_threshold[1]
		self.signalBarThresholdTwo = signal_bar_threshold[2]
		self.signalBarThresholdThree = signal_bar_threshold[3]

	def get_led_dict_values(self):
		dict_values = []
		for x in self.LedDict:
			dict_values.append((x, self.LedDict[x].value()))
		print(dict_values)
		return dict_values

	def set_led_dict_values(self, dict_values):
		print(dict_values)
		for values in dict_values:
			self.LedDict[values[0]].value(values[1])

	def all_off(self):
		# Turn all off
		for x in self.LedDict:
			self.LedDict[x].value(False)
		print('All LEDs Off')

	def all_on(self):
		# Turn all on
		for x in self.LedDict:
			self.LedDict[x].value(True)
		print('All LEDs On')

	def power_on(self, enable=False):
		"""ONE SHOT - Self Stop"""
		if enable:
			read = self.timer.read_ms()
			if 0 <= read < 200:
				if self.printTimes:
					print('[Clock Running] = ON', read, 'ms')
				self.LedDict['P20'].value(True)
			elif 200 <= read < 400:
				if self.printTimes:
					print('[Signal Strength] = ON', read, 'ms')
				self.LedDict['P11'].value(True)
			elif 400 <= read < 600:
				if self.printTimes:
					print('[Clock Running] = OFF', read, 'ms')
				self.LedDict['P20'].value(False)
			elif 600 <= read < 800:
				if self.printTimes:
					print('[Battery Strength] = ON', read, 'ms')
				self.LedDict['P6'].value(True)
			elif 800 <= read < 1000:
				if self.printTimes:
					print('[Strength Bar 1] = ON', read, 'ms')
				self.LedDict['P7'].value(True)
			elif 1000 <= read < 1200:
				if self.printTimes:
					print('[Strength Bar 2] = ON', read, 'ms')
				self.LedDict['P8'].value(True)
			elif 1200 <= read < 1400:
				if self.printTimes:
					print('[Strength Bar 3] = ON', read, 'ms')
				self.LedDict['P9'].value(True)
			elif 1400 <= read < 2000:
				if self.printTimes:
					print('[Strength Bar 4] = ON', read, 'ms')
				self.LedDict['P10'].value(True)
			elif 2000 <= read < 2200:
				if self.printTimes:
					print('[Signal Strength] = OFF', read, 'ms')
				self.LedDict['P11'].value(False)
			elif 2200 <= read < 2400:
				if self.printTimes:
					print('[Battery Strength] = OFF', read, 'ms')
				self.LedDict['P6'].value(False)
			elif 2400 <= read < 2600:
				if self.printTimes:
					print('[Strength Bar 1] = OFF', read, 'ms')
				self.LedDict['P7'].value(False)
			elif 2600 <= read < 2800:
				if self.printTimes:
					print('[Strength Bar 2] = OFF', read, 'ms')
				self.LedDict['P8'].value(False)
			elif 2800 <= read < 3000:
				if self.printTimes:
					print('[Strength Bar 3] = OFF', read, 'ms')
				self.LedDict['P9'].value(False)
			elif 3000 <= read:
				if self.printTimes:
					print('[Strength Bar 4] = OFF', read, 'ms')
				self.LedDict['P10'].value(False)

				self.timer.stop()
				self.timer.reset()
				print('power_on_sequence END')
				enable = False
		return enable

	def power_off(self, enable=False):
		"""ONE SHOT - Self Stop"""
		if enable:
			read = self.timer.read_ms()
			if 0 <= read < 400:
				if self.printTimes:
					print('[Clock Running] = [Signal Strength] = [Battery Strength] = OFF', read, 'ms')
				self.LedDict['P20'].value(False)
				self.LedDict['P11'].value(False)
				self.LedDict['P6'].value(False)
				if self.printTimes:
					print('[Strength Bar 1] = [Strength Bar 2] = [Strength Bar 3] = [Strength Bar 4] = ON')
				self.LedDict['P7'].value(True)
				self.LedDict['P8'].value(True)
				self.LedDict['P9'].value(True)
				self.LedDict['P10'].value(True)
			elif 400 <= read < 800:
				if self.printTimes:
					print('[Signal Strength] = ON', read, 'ms')
				self.LedDict['P11'].value(True)
			elif 800 <= read < 1000:
				if self.printTimes:
					print('[Battery Strength] = ON', read, 'ms')
				self.LedDict['P6'].value(True)
			elif 1000 <= read < 1200:
				if self.printTimes:
					print('[Signal Strength] = OFF', read, 'ms')
				self.LedDict['P11'].value(False)
			elif 1200 <= read < 1400:
				if self.printTimes:
					print('[Battery Strength] = OFF', read, 'ms')
				self.LedDict['P6'].value(False)
			elif 1400 <= read < 1600:
				if self.printTimes:
					print('[Strength Bar 4] = OFF', read, 'ms')
				self.LedDict['P10'].value(False)
			elif 1600 <= read < 1800:
				if self.printTimes:
					print('[Strength Bar 3] = OFF', read, 'ms')
				self.LedDict['P9'].value(False)
			elif 1800 <= read < 2000:
				if self.printTimes:
					print('[Strength Bar 2] = OFF', read, 'ms')
				self.LedDict['P8'].value(False)
			elif 2000 <= read:
				if self.printTimes:
					print('[Strength Bar 1] = OFF', read, 'ms')
				self.LedDict['P7'].value(False)
				self.timer.stop()
				self.timer.reset()
				print('power_off_sequence END')
				enable = False
		return enable

	def searching_for_receiver(self, enable=False):
		"""Repeat this method until it's time to go to sleep or until a Receiver Device is discovered."""
		if enable:
			read = self.timer.read_ms()
			if 0 <= read < 200:
				if self.printTimes:
					print('All LEDs = OFF', read, 'ms')
				self.LedDict['P20'].value(False)
				self.LedDict['P11'].value(False)
				self.LedDict['P6'].value(False)
				self.LedDict['P7'].value(False)
				self.LedDict['P8'].value(False)
				self.LedDict['P9'].value(False)
				self.LedDict['P10'].value(False)
			elif 200 <= read < 700:
				if self.printTimes:
					print('[Signal Strength] = ON', read, 'ms')
				self.LedDict['P11'].value(True)
			elif 700 <= read < 1000:
				if self.printTimes:
					print('[Strength Bar 1] = ON', read, 'ms')
				self.LedDict['P7'].value(True)
			elif 1000 <= read < 1200:
				if self.printTimes:
					print('[Signal Strength] = OFF', read, 'ms')
				self.LedDict['P11'].value(False)
			elif 1200 <= read < 1500:
				if self.printTimes:
					print('[Strength Bar 2] = ON', read, 'ms')
				self.LedDict['P8'].value(True)
			elif 1500 <= read < 1700:
				if self.printTimes:
					print('[Strength Bar 1] = OFF', read, 'ms')
				self.LedDict['P7'].value(False)
			elif 1700 <= read < 2000:
				if self.printTimes:
					print('[Strength Bar 3] = ON', read, 'ms')
				self.LedDict['P9'].value(True)
			elif 2000 <= read < 2200:
				if self.printTimes:
					print('[Strength Bar 2] = OFF', read, 'ms')
				self.LedDict['P8'].value(False)
			elif 2200 <= read < 2500:
				if self.printTimes:
					print('[Strength Bar 4] = ON', read, 'ms')
				self.LedDict['P10'].value(True)
			elif 2500 <= read < 3000:
				if self.printTimes:
					print('[Strength Bar 3] = OFF', read, 'ms')
				self.LedDict['P9'].value(False)
			elif 3000 <= read:
				if self.printTimes:
					print('[Strength Bar 4] = OFF', read, 'ms')
				self.LedDict['P10'].value(False)
				self.timer.reset()
				print('searching_for_receiver_sequence END')
				enable = False
		return enable

	def receiver_discovered(self, enable=False):
		"""ONE SHOT - Self Stop"""
		if enable:
			read = self.timer.read_ms()
			if 0 <= read < 300:
				if self.printTimes:
					print('[Clock Running] = [Battery Strength] = OFF', read, 'ms')
				self.LedDict['P20'].value(False)
				self.LedDict['P6'].value(False)
				if self.printTimes:
					print('[Signal Strength] = [Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = ON')
				self.LedDict['P11'].value(True)
				self.LedDict['P7'].value(True)
				self.LedDict['P8'].value(True)
				self.LedDict['P9'].value(True)
				self.LedDict['P10'].value(True)
			elif 300 <= read < 500:
				if self.printTimes:
					print('[Signal Strength] = [Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = OFF', read, 'ms')
				self.LedDict['P11'].value(False)
				self.LedDict['P7'].value(False)
				self.LedDict['P8'].value(False)
				self.LedDict['P9'].value(False)
				self.LedDict['P10'].value(False)
			elif 500 <= read < 800:
				if self.printTimes:
					print('[Signal Strength] = [Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = ON', read, 'ms')
				self.LedDict['P11'].value(True)
				self.LedDict['P7'].value(True)
				self.LedDict['P8'].value(True)
				self.LedDict['P9'].value(True)
				self.LedDict['P10'].value(True)
			elif 800 <= read < 1000:
				if self.printTimes:
					print('[Signal Strength] = [Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = OFF', read, 'ms')
				self.LedDict['P11'].value(False)
				self.LedDict['P7'].value(False)
				self.LedDict['P8'].value(False)
				self.LedDict['P9'].value(False)
				self.LedDict['P10'].value(False)
			elif 1000 <= read < 1300:
				if self.printTimes:
					print('[Signal Strength] = [Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = ON', read, 'ms')
				self.LedDict['P11'].value(True)
				self.LedDict['P7'].value(True)
				self.LedDict['P8'].value(True)
				self.LedDict['P9'].value(True)
				self.LedDict['P10'].value(True)
			elif 1300 <= read < 1500:
				if self.printTimes:
					print('[Signal Strength] = [Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = OFF', read, 'ms')
				self.LedDict['P11'].value(False)
				self.LedDict['P7'].value(False)
				self.LedDict['P8'].value(False)
				self.LedDict['P9'].value(False)
				self.LedDict['P10'].value(False)
			elif 1500 <= read:
				if self.printTimes:
					print('Normal Signal Strength Mode', read, 'ms')
				self.timer.stop()
				self.timer.reset()
				print('receiver_discovered_sequence END')
				enable = False
		return enable

	def signal_test(self, enable=False, on_off=True, rssi=None):
		"""Continue this method while in this mode (until timeout)"""
		if enable:
			if on_off:
				if self.printTimes:
					print('[Signal Strength] = ON')
				self.LedDict['P11'].value(True)
				if self.printTimes:
					print('[Battery  Strength] = OFF')
				self.LedDict['P6'].value(False)
				if self.printTimes:
					print('[Bar 1], [Bar 2], [Bar 3], [Bar 4] show signal strength -', rssi, 'dB')
				self._set_signal_bars(rssi)
				if self.printTimes:
					print('signal_test_sequence END')
			else:
				if self.printTimes:
					print('[Signal Strength] = OFF')
				self.LedDict['P11'].value(False)
				if self.printTimes:
					print('[Battery  Strength] = OFF')
				self.LedDict['P6'].value(False)
				if self.printTimes:
					print('[Bar 1], [Bar 2], [Bar 3], [Bar 4] = OFF')
				self.LedDict['P10'].value(False)
				self.LedDict['P9'].value(False)
				self.LedDict['P8'].value(False)
				self.LedDict['P7'].value(False)
				if self.printTimes:
					print('signal_test_sequence END')
		return enable

	def _set_signal_bars(self, rssi):
		if rssi > self.signalBarThresholdZero:
			self.LedDict['P10'].value(False)
			self.LedDict['P9'].value(False)
			self.LedDict['P8'].value(False)
			self.LedDict['P7'].value(False)
		elif rssi > self.signalBarThresholdOne:
			self.LedDict['P10'].value(False)
			self.LedDict['P9'].value(False)
			self.LedDict['P8'].value(False)
			self.LedDict['P7'].value(True)
		elif rssi > self.signalBarThresholdTwo:
			self.LedDict['P10'].value(False)
			self.LedDict['P9'].value(False)
			self.LedDict['P8'].value(True)
			self.LedDict['P7'].value(True)
		elif rssi > self.signalBarThresholdThree:
			self.LedDict['P10'].value(False)
			self.LedDict['P9'].value(True)
			self.LedDict['P8'].value(True)
			self.LedDict['P7'].value(True)
		else:
			self.LedDict['P10'].value(True)
			self.LedDict['P9'].value(True)
			self.LedDict['P8'].value(True)
			self.LedDict['P7'].value(True)

	def battery_test(self, enable=False, on_off=True):
		"""Continue this method while in this mode (until timeout)"""
		if enable:
			if on_off:
				vbatt = get_battery_voltage(1)
				if self.printTimes:
					print('[Signal Strength] = OFF')
				self.LedDict['P11'].value(False)
				if self.printTimes:
					print('[Battery  Strength] = ON')
				self.LedDict['P6'].value(True)
				if self.printTimes:
					print('[Bar 1], [Bar 2], [Bar 3], [Bar 4] show battery strength', vbatt, 'V')
				self._set_batt_bars(vbatt)
				if self.printTimes:
					print('battery_test_sequence END')
			else:
				if self.printTimes:
					print('[Signal Strength] = OFF')
				self.LedDict['P11'].value(False)
				if self.printTimes:
					print('[Battery  Strength] = OFF')
				self.LedDict['P6'].value(False)
				if self.printTimes:
					print('[Bar 1], [Bar 2], [Bar 3], [Bar 4] = OFF')
				self.LedDict['P10'].value(False)
				self.LedDict['P9'].value(False)
				self.LedDict['P8'].value(False)
				self.LedDict['P7'].value(False)
				if self.printTimes:
					print('battery_test_sequence END')
		return enable

	def _set_batt_bars(self, vbatt):
		if vbatt > self.battBarThresholdFour:
			self.LedDict['P10'].value(True)
			self.LedDict['P9'].value(True)
			self.LedDict['P8'].value(True)
			self.LedDict['P7'].value(True)
		elif vbatt > self.battBarThresholdThree:
			self.LedDict['P10'].value(False)
			self.LedDict['P9'].value(True)
			self.LedDict['P8'].value(True)
			self.LedDict['P7'].value(True)
		elif vbatt > self.battBarThresholdTwo:
			self.LedDict['P10'].value(False)
			self.LedDict['P9'].value(False)
			self.LedDict['P8'].value(True)
			self.LedDict['P7'].value(True)
		elif vbatt > self.battBarThresholdOne:
			self.LedDict['P10'].value(False)
			self.LedDict['P9'].value(False)
			self.LedDict['P8'].value(False)
			self.LedDict['P7'].value(True)
		else:
			self.LedDict['P10'].value(False)
			self.LedDict['P9'].value(False)
			self.LedDict['P8'].value(False)
			self.LedDict['P7'].value(False)

	def connected_dark(self, enable=False):
		"""Continue this method while still connected"""
		if enable:
			read = self.timer.read_ms()
			if 0 <= read < 4000:
				if self.printTimes:
					print('All LEDs = OFF', read, 'ms')
				self.LedDict['P20'].value(False)
				self.LedDict['P11'].value(False)
				self.LedDict['P6'].value(False)
				self.LedDict['P7'].value(False)
				self.LedDict['P8'].value(False)
				self.LedDict['P9'].value(False)
				self.LedDict['P10'].value(False)
			elif 4000 <= read < 5000:
				if self.printTimes:
					print('[Signal Strength] = ON', read, 'ms')
				self.LedDict['P11'].value(True)
			elif 5000 <= read:
				if self.printTimes:
					print('[Signal Strength] = OFF', read, 'ms')
				self.LedDict['P11'].value(False)
				self.timer.reset()
				if self.printTimes:
					print('connected_dark_sequence END')
		return enable

	def file_transfer(self, enable=False):
		"""Repeat toggle the [Signal Strength] and [Bar 4] LEDs for one cycle or until transfer is complete"""
		if enable:
			read = self.timer.read_ms()
			if 0 <= read < 300:
				if self.printTimes:
					print('[Battery Strength] = [Clock Running] = OFF', read, 'ms')
				self.LedDict['P6'].value(False)
				self.LedDict['P20'].value(False)
				if self.printTimes:
					print('[Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = OFF')
				self.LedDict['P7'].value(False)
				self.LedDict['P8'].value(False)
				self.LedDict['P9'].value(False)
				self.LedDict['P10'].value(False)
				if self.printTimes:
					print('[Signal Strength] = ON')
				self.LedDict['P11'].value(True)
			elif 300 <= read < 500:
				if self.printTimes:
					print('[Bar 4] = ON', read, 'ms')
				self.LedDict['P10'].value(False)
			elif 500 <= read < 800:
				if self.printTimes:
					print('[Signal Strength] = OFF', read, 'ms')
				self.LedDict['P11'].value(False)
			elif 800 <= read < 1000:
				if self.printTimes:
					print('[Bar 4] = OFF', read, 'ms')
				self.LedDict['P10'].value(False)
			elif 1000 <= read:
				self.timer.reset()
				self.transfer_cycle_flag = True
				print('file_transfer_sequence END')
		return enable

	def time_of_day(self, enable=False):
		"""
		Repeat toggling the [Clock Running] LED until KD enters Connected Dark Sequence or until RD exits Time of Day Mode
		"""
		if enable:
			read = self.timer.read_ms()
			if 0 <= read < 1000:
				if self.printTimes:
					print('All LEDs = OFF', read, 'ms')
				self.LedDict['P20'].value(False)
				self.LedDict['P11'].value(False)
				self.LedDict['P6'].value(False)
				self.LedDict['P7'].value(False)
				self.LedDict['P8'].value(False)
				self.LedDict['P9'].value(False)
				self.LedDict['P10'].value(False)
			elif 1000 <= read < 1800:
				if self.printTimes:
					print('[Clock Running] = ON', read, 'ms')
				self.LedDict['P20'].value(True)
			elif 1800 <= read < 3000:
				if self.printTimes:
					print('[Clock Running] = OFF', read, 'ms')
				self.LedDict['P20'].value(False)
			elif 3000 <= read < 3800:
				if self.printTimes:
					print('[Clock Running] = ON', read, 'ms')
				self.LedDict['P20'].value(True)
			elif 3800 <= read:
				if self.printTimes:
					print('[Clock Running] = OFF', read, 'ms')
				self.LedDict['P20'].value(False)
				self.timer.reset()
				if self.printTimes:
					print('time_of_day_sequence END')
		return enable
