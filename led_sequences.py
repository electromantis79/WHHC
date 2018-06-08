from machine import Timer


class LedSequences(object):
	"""methods must be called from inside a loop to be called faster than or equal to the 50ms minimum"""

	def __init__(self, led_dict):
		self.LedDict = led_dict
		self.timer = Timer.Chrono()
	
	def power_on(self, enable=False):
		"""ONE SHOT - Self Stop"""
		if enable:
			read = self.timer.read_ms()
			if 0 <= read < 250:
				print('[Clock Running] = ON', read, 'ms')
			elif 250 <= read < 300:
				print('[Signal Strength] = ON', read, 'ms')
			elif 300 <= read < 500:
				print('[Clock Running] = OFF', read, 'ms')
			elif 500 <= read < 750:
				print('[Battery Strength] = ON', read, 'ms')
			elif 750 <= read < 1000:
				print('[Strength Bar 1] = ON', read, 'ms')
			elif 1000 <= read < 1250:
				print('[Strength Bar 2] = ON', read, 'ms')
			elif 1250 <= read < 1500:
				print('[Strength Bar 3] = ON', read, 'ms')
			elif 1500 <= read < 1750:
				print('[Strength Bar 4] = ON', read, 'ms')
			elif 1750 <= read < 2000:
				print('[Signal Strength] = OFF', read, 'ms')
			elif 2000 <= read < 2250:
				print('[Battery Strength] = OFF', read, 'ms')
			elif 2250 <= read < 2500:
				print('[Strength Bar 1] = OFF', read, 'ms')
			elif 2500 <= read < 2750:
				print('[Strength Bar 2] = OFF', read, 'ms')
			elif 2750 <= read < 3000:
				print('[Strength Bar 3] = OFF', read, 'ms')
			elif 3000 <= read:
				print('[Strength Bar 4] = OFF', read, 'ms')
				self.timer.stop()
				self.timer.reset()
				print('power_on_sequence END')
				enable = False
		return enable

	def power_off(self, enable=False):
		"""ONE SHOT - Self Stop"""
		if enable:
			read = self.timer.read_ms()
			if 0 <= read < 250:
				print('[Clock Running] = [Signal Strength] = [Battery Strength] = OFF', read, 'ms')
				print('[Strength Bar 1] = [Strength Bar 2] = [Strength Bar 3] = [Strength Bar 4] = ON')
			elif 250 <= read < 500:
				print('[Signal Strength] = ON', read, 'ms')
			elif 500 <= read < 750:
				print('[Battery Strength] = ON', read, 'ms')
			elif 750 <= read < 1000:
				print('[Signal Strength] = OFF', read, 'ms')
			elif 1000 <= read < 1250:
				print('[Battery Strength] = OFF', read, 'ms')
			elif 1250 <= read < 1500:
				print('[Strength Bar 4] = OFF', read, 'ms')
			elif 1500 <= read < 1750:
				print('[Strength Bar 3] = OFF', read, 'ms')
			elif 1750 <= read < 2000:
				print('[Strength Bar 2] = OFF', read, 'ms')
			elif 2000 <= read:
				print('[Strength Bar 1] = OFF', read, 'ms')
				self.timer.stop()
				self.timer.reset()
				print('power_off_sequence END')
				enable = False
		return enable

	def searching_for_receiver(self, enable=False):
		"""Repeat this method until it's time to go to sleep or until a Receiver Device is discovered."""
		if enable:
			read = self.timer.read_ms()
			if 0 <= read < 250:
				print('All LEDs = OFF', read, 'ms')
			elif 250 <= read < 750:
				print('[Signal Strength] = ON', read, 'ms')
			elif 750 <= read < 1000:
				print('[Strength Bar 1] = ON', read, 'ms')
			elif 1000 <= read < 1250:
				print('[Signal Strength] = OFF', read, 'ms')
			elif 1250 <= read < 1500:
				print('[Strength Bar 2] = ON', read, 'ms')
			elif 1500 <= read < 1750:
				print('[Strength Bar 1] = OFF', read, 'ms')
			elif 1750 <= read < 2000:
				print('[Strength Bar 3] = ON', read, 'ms')
			elif 2000 <= read < 2250:
				print('[Strength Bar 2] = OFF', read, 'ms')
			elif 2250 <= read < 2500:
				print('[Strength Bar 4] = ON', read, 'ms')
			elif 2500 <= read < 3000:
				print('[Strength Bar 3] = OFF', read, 'ms')
			elif 3000 <= read:
				print('[Strength Bar 4] = OFF', read, 'ms')
				self.timer.reset()
				print('searching_for_receiver_sequence END')
				enable = False
		return enable

	def receiver_discovered(self, enable=False):
		"""ONE SHOT - Self Stop"""
		if enable:
			read = self.timer.read_ms()
			if 0 <= read < 250:
				print('[Clock Running] = [Battery Strength] = OFF', read, 'ms')
				print('[Signal Strength] = [Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = ON')
			elif 250 <= read < 500:
				print('[Signal Strength] = [Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = OFF', read, 'ms')
			elif 500 <= read < 750:
				print('[Signal Strength] = [Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = ON', read, 'ms')
			elif 750 <= read < 1000:
				print('[Signal Strength] = [Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = OFF', read, 'ms')
			elif 1000 <= read < 1250:
				print('[Signal Strength] = [Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = ON', read, 'ms')
			elif 1250 <= read < 1500:
				print('[Signal Strength] = [Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = OFF', read, 'ms')
			elif 1500 <= read:
				print('Normal Signal Strength Mode', read, 'ms')
				self.timer.stop()
				self.timer.reset()
				print('receiver_discovered_sequence END')
				enable = False
		return enable

	def battery_test(self, enable=False):
		"""Continue this method while in this mode (until timeout)"""
		if enable:
			print('[Signal Strength] = OFF')
			print('[Battery  Strength] = ON')
			print('[Bar 1], [Bar 2], [Bar 3], [Bar 4] show battery strength')
			print('battery_test_sequence END')
		return enable

	def connected_dark(self, enable=False):
		"""Continue this method while still connected"""
		if enable:
			read = self.timer.read_ms()
			if 0 <= read < 4000:
				print('All LEDs = OFF', read, 'ms')
			elif 4000 <= read < 5000:
				print('[Signal Strength] = ON', read, 'ms')
			elif 5000 <= read:
				print('[Signal Strength] = OFF', read, 'ms')
				self.timer.reset()
				print('connected_dark_sequence END')
		return enable

	def file_transfer(self, enable=False):
		"""Repeat toggle the [Signal Strength] and [Bar 4] LEDs until transfer is complete"""
		if enable:
			read = self.timer.read_ms()
			if 0 <= read < 250:
				print('[Battery Strength] = [Clock Running] = OFF', read, 'ms')
				print('[Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = OFF')
				print('[Signal Strength] = ON')
			elif 250 <= read < 500:
				print('[Bar 4] = ON', read, 'ms')
			elif 500 <= read < 750:
				print('[Signal Strength] = OFF', read, 'ms')
			elif 750 <= read:
				print('[Bar 4] = OFF', read, 'ms')
				self.timer.reset()
				print('file_transfer_sequence END')
		return enable

	def time_of_day(self, enable=False):
		"""
		Repeat toggling the [Clock Running] LED until KD enters Connected Dark Sequence or until RD exits Time of Day Mode
		"""
		if enable:
			read = self.timer.read_ms()
			if 0 <= read < 1000:
				print('All LEDs = OFF', read, 'ms')
			elif 1000 <= read < 1750:
				print('[Clock Running] = ON', read, 'ms')
			elif 1750 <= read < 3000:
				print('[Clock Running] = OFF', read, 'ms')
			elif 3000 <= read < 3750:
				print('[Clock Running] = ON', read, 'ms')
			elif 3750 <= read:
				print('[Clock Running] = OFF', read, 'ms')
				self.timer.reset()
				print('time_of_day_sequence END')
		return enable
