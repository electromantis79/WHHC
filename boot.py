# boot.py -- run on boot-up
# can run arbitrary Python, but best to keep it minimal

from network import WLAN
from machine import UART
from os import dupterm
import time
import os
import machine, sys

SSID = 'Pi3_AP'
AUTH = (WLAN.WPA2, 'raspberry')

# enable the UART on the USB-to-serial port
uart = UART(0, baudrate=115200)

# duplicate the terminal on the UART
dupterm(uart)
print('\nUART initialised\n')
print('Python version', sys.version)
print('Unique ID',machine.unique_id())

# login to the local network
if machine.reset_cause() != machine.SOFT_RESET:
	print('Initialising WLAN in station mode...', end=' ')
	wlan = WLAN(0,WLAN.STA)
	print('done.\nConnecting to WiFi network...', end='')
	wlan.ifconfig(config='dhcp')
	wlan.connect(ssid=SSID, auth=AUTH)
	while not wlan.isconnected():
		machine.idle()
		time.sleep_ms(500)
		print('.', end='')
		machine.idle()
	print(' done.\n')

	ip, mask, gateway, dns = wlan.ifconfig()
	print('IP address: ', ip)
	print('Netmask:    ', mask)
	print('Gateway:    ', gateway)
	print('DNS:        ', dns)
	print()
else:
	wlan=WLAN()
	print ('Wireless still connected =', wlan.isconnected(), '\n')
	if wlan.isconnected():
		ip, mask, gateway, dns = wlan.ifconfig()
		print('IP address: ', ip)
		print('Netmask:    ', mask)
		print('Gateway:    ', gateway)
		print('DNS:        ', dns)
		print()
