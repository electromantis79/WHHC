import socket
import machine
import math
import time
import json


def check_receive(sock, mode):
	# print('\nenter check_receive')
	data = None
	try:
		data = sock.recv(4096)

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

	if data is not None:
		data = decode_bytes_to_string(data)

	if data:
		print('Data Received', data)

	return sock, data, mode


def check_led_data(data, led_dict, led_pin_vs_number_list):
	print('\nDATA in check_led_data is', data)
	if data[0] == '$':
		# $ = led data
		data = data[1:]
		length = len(data) / 3
		print(length)
		print(data[0] == 'L')
		print(data[1] in list(['1', '2', '3', '4', '5', '6', '7']))
		byte_index = 0
		for leds in list(range(int(length-1))):
			print(byte_index, leds)
			if data[byte_index] == '$':
				byte_index = 0

			if data[0+byte_index] == 'L' and data[1+byte_index] in list(['1', '2', '3', '4', '5', '6', '7']):
				for pair in led_pin_vs_number_list:
					if data[1+byte_index] == pair[1]:
						if data[2+byte_index] == '1':
							print(data[0+byte_index:2+byte_index], 'led True', data[2+byte_index])
							led_dict[pair[0]].value(True)
						elif data[2+byte_index] == '0':
							print(data[0+byte_index:2+byte_index], 'led False', data[2+byte_index])
							led_dict[pair[0]].value(False)
						else:
							print('check_led_data packet format error of', data[2+byte_index])
				byte_index += 3
			else:
				continue


def decode_bytes_to_string(data):
	string = ''
	for x, y in enumerate(data):
		z = chr(data[x])
		string = string + z
	return string


def handle_button_event(json_tree, butt_event_dict):
	for button in butt_event_dict:
		if butt_event_dict[button]:
			if butt_event_dict[button] == 1:
				butt_event_dict[button] = 2
				json_tree['button_objects'][button]['event_flag'] = True
				json_tree['button_objects'][button]['event_state'] = 'down'
			elif butt_event_dict[button] == 3:
				butt_event_dict[button] = 0
				json_tree['button_objects'][button]['event_flag'] = True
				json_tree['button_objects'][button]['event_state'] = 'up'

	return json_tree


def send_button_events(sock, json_tree, mode):
	temp_dict = dict()
	for button in json_tree['button_objects'].keys():
		if button[0] == 'P' and json_tree['button_objects'][button]['event_flag']:
			temp_dict['button_objects'] = dict()
			temp_dict['button_objects'][button] = dict()
			temp_dict['button_objects'][button]['event_flag'] = json_tree['button_objects'][button]['event_flag']
			temp_dict['button_objects'][button]['event_state'] = json_tree['button_objects'][button]['event_state']
			temp_dict['button_objects'][button]['keymap_grid_value'] = json_tree['button_objects'][button]['keymap_grid_value']
			json_tree['button_objects'][button]['event_flag'] = False

	if temp_dict:
		# Send some data to remote server
		# Connect to remote server
		json_string = json.dumps(temp_dict)
		try:
			# Send the whole string
			sock.sendall(json_string)
			print('Sent', json_string)

		except OSError as err:
			if err.errno == 104:  # ECONNRESET
				print("send_button_events OS error ECONNRESET:", err)
			else:
				print("send_button_events OS error:", err)

			mode = 'SearchModes'
			print('\n======== END Connected Modes ========\n')
			print('\n======== BEGIN Search Modes ========\n')

	return sock, json_tree, mode


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
	adcread = adc.channel(attn=2, pin='P19')
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
		if mean_adc:
			print("10**6*Variance/(Mean**2) of ADC readings = %15.13f" % ((variance_adc*10**6)//(mean_adc**2)))
		else:
			print("10**6*Variance/(Mean**2) of ADC readings = %15.13f" % mean_adc)
		print("Battery voltage = %15.13f" % vbatt)
	return vbatt


def build_json_tree(
		led_dict, button_dict, led_info_dict, button_info_dict):
	json_tree = dict()
	json_tree['object_type'] = 'Pin'
	json_tree['led_objects'] = dict()
	json_tree['led_objects']['component_type'] = 'led'
	for led in led_dict:
		json_tree['led_objects'][led] = dict()
		json_tree['led_objects'][led]['value'] = led_dict[led].value()
		json_tree['led_objects'][led]['mode'] = led_dict[led].mode()
		json_tree['led_objects'][led]['pull'] = led_dict[led].pull()
		json_tree['led_objects'][led]['keypad_pin_number'] = led_info_dict[led]['keypad_pin_number']
		json_tree['led_objects'][led]['led_id'] = led_info_dict[led]['led_id']
		json_tree['led_objects'][led]['function_name'] = led_info_dict[led]['function_name']

	json_tree['button_objects'] = dict()
	json_tree['button_objects']['component_type'] = 'button'
	for button in button_dict:
		json_tree['button_objects'][button] = dict()
		json_tree['button_objects'][button]['value'] = button_dict[button].value()
		json_tree['button_objects'][button]['mode'] = button_dict[button].mode()
		json_tree['button_objects'][button]['pull'] = button_dict[button].pull()
		json_tree['button_objects'][button]['keypad_pin_number'] = button_info_dict[button]['keypad_pin_number']
		json_tree['button_objects'][button]['button_id'] = button_info_dict[button]['button_id']
		json_tree['button_objects'][button]['function_name'] = button_info_dict[button]['function_name']
		json_tree['button_objects'][button]['keypad_key_number'] = button_info_dict[button]['keypad_key_number']
		json_tree['button_objects'][button]['keymap_grid_value'] = button_info_dict[button]['keymap_grid_value']
		json_tree['button_objects'][button]['event_flag'] = False
		json_tree['button_objects'][button]['event_state'] = 'up'

	return json_tree
