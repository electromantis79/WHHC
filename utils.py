import socket
import machine
import math
import time


def check_receive(sock, mode):
	data = None
	try:
		data = sock.recv(4096)
		if data:
			data = decode_bytes_to_string(data)
			print('Data Received', data)

	except OSError as err:
		# print (err, err.errno)

		if err.errno == 11:
			# Don't care about error here. It is normal for .recv() if non-blocking to wait for device to be ready
			print('special 11 spot', err)
		elif err.errno == 113:
			print("check_receive OS error:", err)
		elif err.errno == 104:  # ECONNRESET
			print("check_receive OS error ECONNRESET:", err)
		else:
			print("check_receive OS error GENERIC:", err)
		mode = 'SearchModes'
		print('\n======== END Connected Modes ========\n')
		print('\n======== BEGIN Search Modes ========\n')

	return sock, data, mode


def decode_bytes_to_string(data):
	string = ''
	for x, y in enumerate(data):
		z = chr(data[x])
		string = string + z
	return string


def handle_button_event(butt_event_dict, key_map_dict):
	button_events_string = None
	for button in butt_event_dict:
		if butt_event_dict[button]:
			if butt_event_dict[button] == 1:
				direction = 'D'
				butt_event_dict[button] = 2
				button_events_string = str(key_map_dict[button]) + direction
			elif butt_event_dict[button] == 3:
				direction = 'U'
				butt_event_dict[button] = 0
				button_events_string = str(key_map_dict[button]) + direction

	return button_events_string


def send_button_events(sock, message, mode):
	if message:
		# Send some data to remote server
		# Connect to remote server
		try:
			# Send the whole string
			sock.sendall(message)
			print('Sent', message)

		except OSError as err:
			if err.errno == 104:  # ECONNRESET
				print("send_button_events OS error ECONNRESET:", err)
			else:
				print("send_button_events OS error:", err)

			mode = 'SearchModes'
			print('\n======== END Connected Modes ========\n')
			print('\n======== BEGIN Search Modes ========\n')

	return sock, mode


def get_rssi(wlan):
	nets = wlan.scan()
	rssi = None
	for net in nets:
		if net.ssid == 'ScoreNet':
			rssi = net.rssi
			rssi = str(rssi)[1:]
			print('RSSI =', rssi)

	return rssi


def get_battery_voltage(show=0):
	"""
	typedef enum {
		ADC_ATTEN_0DB = 0,
		ADC_ATTEN_3DB, // 1
		ADC_ATTEN_6DB, // 2
		ADC_ATTEN_12DB, // 3
		ADC_ATTEN_MAX, // 4
	} adc_atten_t;
	"""
	number_of_adc_readings = const(100)
	adc = machine.ADC(0)
	adcread = adc.channel(attn=2, pin='P16')
	samples_adc = [0.0]*number_of_adc_readings
	mean_adc = 0.0
	i = 0
	while i < number_of_adc_readings:
		adcint = adcread()
		samples_adc[i] = adcint
		mean_adc += adcint
		i += 1
	mean_adc /= number_of_adc_readings
	variance_adc = 0.0
	for adcint in samples_adc:
		variance_adc += (adcint - mean_adc)**2
	variance_adc /= (number_of_adc_readings - 1)
	vbatt = ((mean_adc/3)*1400/1024)*171/(56*1000)  # Vbatt=Vmeasure*((115+56)/56)
	if show:
		print("%u ADC readings :\n%s" % (number_of_adc_readings, str(samples_adc)))
		print("Mean of ADC readings (0-4095) = %15.13f" % mean_adc)
		print("Mean of ADC readings (0-1846 mV) = %15.13f" % (mean_adc*1846/4096))  # Calibrated manually
		print("Variance of ADC readings = %15.13f" % variance_adc)
		print("Standard Deviation of ADC readings = %15.13f" % math.sqrt(variance_adc))
		print("10**6*Variance/(Mean**2) of ADC readings = %15.13f" % ((variance_adc*10**6)//(mean_adc**2)))
		print("Battery voltage = %15.13f" % vbatt)
	return vbatt
