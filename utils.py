import socket
import machine
import math
import time


def connect_socket(host, port):
	try:
		# Create an AF_INET, STREAM socket (TCP)
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except OSError as err:
		print("connect_socket OS error:", err)
		print('Failed to create socket.')
		machine.reset()

	print('Socket Created')

	try:
		sock.connect((host, port))
		sock.setblocking(0)
	except OSError as err:
		print("connect_socket OS error:", err)
		print('Failed to connect to ' + host)
		machine.reset()

	print('Socket Connected to ' + host + ' on port ' + str(port))
	return sock


def check_receive(sock, host, port):
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
			pass
		elif err.errno == 113:
			print("check_receive OS error:", err)
			machine.reset()
		elif err.errno == 104:  # ECONNRESET
			print("check_receive OS error ECONNRESET:", err)
			time.sleep_us(10)
			sock = connect_socket(host, port)
		else:
			print("check_receive OS error GENERIC:", err)
			machine.reset()
	return sock, data


def decode_bytes_to_string(data):
	string = ''
	for x, y in enumerate(data):
		z = chr(data[x])
		string = string + z
	return string


def send_button_press(sock, host, port, butt_event_dict, key_map_dict):
	message = None
	for button in butt_event_dict:
		if butt_event_dict[button]:
			if butt_event_dict[button] == 1:
				direction = 'D'
				butt_event_dict[button] = 2
				message = str(key_map_dict[button]) + direction
			elif butt_event_dict[button] == 3:
				direction = 'U'
				butt_event_dict[button] = 0
				message = str(key_map_dict[button]) + direction

			if message:
				# Send some data to remote server
				# Connect to remote server
				try:
					# Send the whole string
					sock.sendall(message)
					print('Sent', message)
					message = 0
				except OSError as err:
					if err.errno == 104:  # ECONNRESET
						print("send_button_press OS error ECONNRESET:", err)
						time.sleep_us(10)
						sock = connect_socket(host, port)
					else:
						print("send_button_press OS error:", err)
						machine.reset()
	return sock, message


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
