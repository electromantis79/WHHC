import time
import json

from math import sqrt
from machine import ADC


def convert_packet_to_json_string_fragment(key_map_dict, packet):
	# Decode packet
	button_name = packet[0]

	if packet[1] == 0:
		event_state = 'down'
	elif packet[1] == 1:
		event_state = 'up'
	else:
		event_state = 'error'

	event_time = packet[2]

	# Build temp_dict
	temp_dict = dict()
	temp_dict['button_objects'] = dict()
	temp_dict['button_objects'][button_name] = dict()
	temp_dict['button_objects'][button_name]['event_flag'] = True
	temp_dict['button_objects'][button_name]['event_state'] = event_state
	temp_dict['button_objects'][button_name]['event_time'] = event_time
	temp_dict['button_objects'][button_name]['keymap_grid_value'] = key_map_dict[button_name]

	# Convert to json
	json_string = json.dumps(temp_dict)

	# Add header
	json_string_fragment = 'JSON_FRAGMENT' + json_string

	return json_string_fragment


def build_rssi_json_string_fragment(value):
	temp_dict = dict()
	temp_dict['rssi'] = value
	json_string = json.dumps(temp_dict)
	json_string_fragment = 'JSON_FRAGMENT' + json_string
	return json_string_fragment


def send_events(sock, json_string, mode, print_flag=False):
	need_acknowledgement_flag = False
	if json_string:
		# Send some data to remote server
		# Connect to remote server
		tic = time.ticks_us() / 1000
		# print('Send START', tic, 'ms')

		try:
			# Send the whole string
			sock.sendall(json_string)
			toc = time.ticks_us() / 1000
			need_acknowledgement_flag = True
			if print_flag:
				print('\n        Send END', toc, 'ms, Dif send', toc - tic, 'ms:', json_string)

		except OSError as err:
			if err.errno == 104:  # ECONNRESET
				print("        send_button_events OS error ECONNRESET:", err)
			else:
				print("        send_button_events OS error:", err)
			need_acknowledgement_flag = False

			mode = 'SearchModes'
			print('\n======== END Connected Modes ========\n')
			print('\n======== BEGIN Search Modes ========\n')

	return need_acknowledgement_flag, sock, mode


def check_receive(sock, mode, socket_created_flag, print_flag=False):
	# print('\nenter check_receive')
	data = None
	try:
		tic = time.ticks_us() / 1000
		# print('Read START', tic, 'ms')
		data = sock.read()
		toc = time.ticks_us() / 1000
		# print('Read END', toc, 'ms')

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

		sock.close()
		socket_created_flag = False

		print('\n======== END Connected Modes ========\n')
		print('\n======== BEGIN Search Modes ========\n')

	if data is not None:
		data = decode_bytes_to_string(data)

	if data:
		if print_flag:
			print('\nData Received', time.ticks_us() / 1000, 'ms,', 'Dif read', toc-tic, 'ms:',  data)

	return sock, data, mode, socket_created_flag


def decode_bytes_to_string(data):
	string = ''
	for x, y in enumerate(data):
		z = chr(data[x])
		string = string + z
	return string


def find_substrings(string, substring, print_flag=False):
	count = 0
	index = 0
	flag = True
	index_list = list()
	while flag:
		a = string.find(substring, index)
		if a == -1:
			flag = False
		else:
			count += 1
			index_list.append(a)
			index = a + 1
	if print_flag:
		print('index_list', index_list)
	return index_list


def slice_fragments(data, index_list):
	fragment_list = list()
	for count in list(range(len(index_list))):
		if len(index_list) == 1:
			fragment_list.append(data)
		elif count == len(index_list) - 1:
			fragment_list.append(data[index_list[-1]:])
		else:
			fragment_list.append(data[index_list[count]:index_list[count+1]])

	for fragment_index, fragment in enumerate(fragment_list):
		fragment_list[fragment_index] = fragment[len('JSON_FRAGMENT'):]

	# print('fragment_list', fragment_list)
	return fragment_list


def convert_to_json_format(data):
	try:
		data = json.loads(data)
		return data
	except Exception as e:
		print('\n', e, ': Data received failed json format inspection')
		return False


def check_led_data(json_tree_fragment_dict, led_dict, print_flag=False):
	if json_tree_fragment_dict is not None:
		if 'led_objects' in json_tree_fragment_dict:
			for led in json_tree_fragment_dict['led_objects']:
				if 'value' in json_tree_fragment_dict['led_objects'][led]:
					# print('\npin', led, 'is', json_tree_fragment_dict['led_objects'][led]['value'])
					if json_tree_fragment_dict['led_objects'][led]['value']:
						led_dict[led].value(True)
					else:
						led_dict[led].value(False)
				else:
					if print_flag:
						print("\n'value' key is not in fragment of led dictionary",	led)
		else:
			if print_flag:
				print('\nled_objects not in fragment')

	return led_dict


def check_command_flags(json_tree_fragment_dict, json_tree, flag_list, print_flag=False):
	if json_tree_fragment_dict is not None:
		if 'command_flags' in json_tree_fragment_dict:
			for flag in flag_list:
				if flag in json_tree_fragment_dict['command_flags']:
					json_tree['command_flags'][flag] = json_tree_fragment_dict['command_flags'][flag]
				else:
					if print_flag:
						print('\n', flag, ' not in command_flags')
		else:
			if print_flag:
				print('\ncommand_flags not in fragment')

	return json_tree


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
	adc = ADC(0)
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
		print("Standard Deviation of ADC readings = %15.13f" % sqrt(variance_adc))
		if mean_adc:
			print("10**6*Variance/(Mean**2) of ADC readings = %15.13f" % ((variance_adc*10**6)//(mean_adc**2)))
		else:
			print("10**6*Variance/(Mean**2) of ADC readings = %15.13f" % mean_adc)
		print("Battery voltage = %15.13f" % vbatt)
	return vbatt


def validate_ptp_string(data, header_string, print_messages):
	header_length = len(header_string)
	time_stamp = 0
	if print_messages:
		print('data:', data, 'header_string', header_string)
	data = data[header_length:]
	try:
		time_stamp = int(data)
		valid = True
	except:
		valid = False

	return valid, time_stamp


def toggle_pin_ms(time_pin, duration=1, repeat_quantity=1):
	for toggle in range(repeat_quantity):
		time_pin.value(True)
		time.sleep_ms(duration)
		time_pin.value(False)
		time.sleep_ms(duration)


def calculate_time_values(time_1, time_2, time_3, time_4, print_messages=False):
	if print_messages:
		print('time_1', time_1, 'time_2', time_2, 'time_3', time_3, 'time_4', time_4)
	MS_diff = time_2 - time_1
	SM_diff = time_4 - time_3
	offset = int((MS_diff - SM_diff) / 2)
	one_way_delay = int((MS_diff + SM_diff) / 2)
	if print_messages:
		print('MS_diff', MS_diff, 'SM_diff', SM_diff, 'offset', offset, 'one_way_delay', one_way_delay)
	return offset, one_way_delay


def get_ticks_us(offset):
	return time.ticks_us() - offset


def build_json_tree(
		led_dict, button_dict, led_info_dict, button_info_dict, flag_list):
	json_tree = dict()
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
		json_tree['button_objects'][button]['event_time'] = 0
		json_tree['button_objects'][button]['event_state'] = 'up'

	json_tree['command_flags'] = dict()
	for flag in flag_list:
		json_tree['command_flags'][flag] = False

	json_tree['rssi'] = None
	return json_tree
