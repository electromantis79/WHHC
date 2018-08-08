from machine import Timer


class LedSequences(object):
	"""methods must be called from inside a loop to be called faster than or equal to the 50ms minimum"""

	def __init__(self, led_dict):
		self.LedDict = led_dict
		self.timer = Timer.Chrono()
		self.transfer_cycle_flag = False
	
	def power_on(self, enable=False):
		"""ONE SHOT - Self Stop"""
		if enable:
			read = self.timer.read_ms()
			if 0 <= read < 200:
				print('[Clock Running] = ON', read, 'ms')
			elif 200 <= read < 400:
				print('[Signal Strength] = ON', read, 'ms')
			elif 400 <= read < 600:
				print('[Clock Running] = OFF', read, 'ms')
			elif 600 <= read < 800:
				print('[Battery Strength] = ON', read, 'ms')
			elif 800 <= read < 1000:
				print('[Strength Bar 1] = ON', read, 'ms')
			elif 1000 <= read < 1200:
				print('[Strength Bar 2] = ON', read, 'ms')
			elif 1200 <= read < 1400:
				print('[Strength Bar 3] = ON', read, 'ms')
			elif 1400 <= read < 2000:
				print('[Strength Bar 4] = ON', read, 'ms')
			elif 2000 <= read < 2200:
				print('[Signal Strength] = OFF', read, 'ms')
			elif 2200 <= read < 2400:
				print('[Battery Strength] = OFF', read, 'ms')
			elif 2400 <= read < 2600:
				print('[Strength Bar 1] = OFF', read, 'ms')
			elif 2600 <= read < 2800:
				print('[Strength Bar 2] = OFF', read, 'ms')
			elif 2800 <= read < 3000:
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
			if 0 <= read < 400:
				print('[Clock Running] = [Signal Strength] = [Battery Strength] = OFF', read, 'ms')
				print('[Strength Bar 1] = [Strength Bar 2] = [Strength Bar 3] = [Strength Bar 4] = ON')
			elif 400 <= read < 800:
				print('[Signal Strength] = ON', read, 'ms')
			elif 800 <= read < 1000:
				print('[Battery Strength] = ON', read, 'ms')
			elif 1000 <= read < 1200:
				print('[Signal Strength] = OFF', read, 'ms')
			elif 1200 <= read < 1400:
				print('[Battery Strength] = OFF', read, 'ms')
			elif 1400 <= read < 1600:
				print('[Strength Bar 4] = OFF', read, 'ms')
			elif 1600 <= read < 1800:
				print('[Strength Bar 3] = OFF', read, 'ms')
			elif 1800 <= read < 2000:
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
			if 0 <= read < 200:
				print('All LEDs = OFF', read, 'ms')
			elif 200 <= read < 700:
				print('[Signal Strength] = ON', read, 'ms')
			elif 700 <= read < 1000:
				print('[Strength Bar 1] = ON', read, 'ms')
			elif 1000 <= read < 1200:
				print('[Signal Strength] = OFF', read, 'ms')
			elif 1200 <= read < 1500:
				print('[Strength Bar 2] = ON', read, 'ms')
			elif 1500 <= read < 1700:
				print('[Strength Bar 1] = OFF', read, 'ms')
			elif 1700 <= read < 2000:
				print('[Strength Bar 3] = ON', read, 'ms')
			elif 2000 <= read < 2200:
				print('[Strength Bar 2] = OFF', read, 'ms')
			elif 2200 <= read < 2500:
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
			if 0 <= read < 300:
				print('[Clock Running] = [Battery Strength] = OFF', read, 'ms')
				print('[Signal Strength] = [Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = ON')
			elif 300 <= read < 500:
				print('[Signal Strength] = [Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = OFF', read, 'ms')
			elif 500 <= read < 800:
				print('[Signal Strength] = [Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = ON', read, 'ms')
			elif 800 <= read < 1000:
				print('[Signal Strength] = [Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = OFF', read, 'ms')
			elif 1000 <= read < 1300:
				print('[Signal Strength] = [Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = ON', read, 'ms')
			elif 1300 <= read < 1500:
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
		"""Repeat toggle the [Signal Strength] and [Bar 4] LEDs for one cycle or until transfer is complete"""
		if enable:
			read = self.timer.read_ms()
			if 0 <= read < 300:
				print('[Battery Strength] = [Clock Running] = OFF', read, 'ms')
				print('[Bar 1] = [Bar 2] = [Bar 3] = [Bar 4] = OFF')
				print('[Signal Strength] = ON')
			elif 300 <= read < 500:
				print('[Bar 4] = ON', read, 'ms')
			elif 500 <= read < 800:
				print('[Signal Strength] = OFF', read, 'ms')
			elif 800 <= read < 1000:
				print('[Bar 4] = OFF', read, 'ms')
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
				print('All LEDs = OFF', read, 'ms')
			elif 1000 <= read < 1800:
				print('[Clock Running] = ON', read, 'ms')
			elif 1800 <= read < 3000:
				print('[Clock Running] = OFF', read, 'ms')
			elif 3000 <= read < 3800:
				print('[Clock Running] = ON', read, 'ms')
			elif 3800 <= read:
				print('[Clock Running] = OFF', read, 'ms')
				self.timer.reset()
				print('time_of_day_sequence END')
		return enable
