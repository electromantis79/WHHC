
class LedSequences(object):
	"""methods must be called from inside a loop to be called faster than or equal to the 50ms minimum"""

	def __init__(self, led_dict):
		self.LedDict = led_dict

	def power_on_sequence(self, timer, enable):
		if enable:
			read = timer.read_ms()
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
				timer.stop()
				timer.reset()
				print('power_on_sequence END')
				enable = False
		return timer, enable

	def power_off_sequence(self, timer, enable):
		if enable:
			read = timer.read_ms()
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
				timer.stop()
				timer.reset()
				print('power_off_sequence END')
				enable = False
		return timer, enable
