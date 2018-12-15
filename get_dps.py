#!/usr/bin/python3

########################################################################################
# 	Domoticz Tuya Smart Plug Python Plugin                                             #
#                                                                                      #
# 	MIT License                                                                        #
#                                                                                      #
#	Copyright (c) 2018 tixi                                                            #
#                                                                                      #
#	Permission is hereby granted, free of charge, to any person obtaining a copy       #
#	of this software and associated documentation files (the "Software"), to deal      #
#	in the Software without restriction, including without limitation the rights       #
#	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell          #
#	copies of the Software, and to permit persons to whom the Software is              #
#	furnished to do so, subject to the following conditions:                           #
#                                                                                      #
#	The above copyright notice and this permission notice shall be included in all     #
#	copies or substantial portions of the Software.                                    #
#                                                                                      #
#	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR         #
#	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,           #
#	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE        #
#	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER             #
#	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,      #
#	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE      #
#	SOFTWARE.                                                                          #
#                                                                                      #
########################################################################################

import sys
import pytuya
import socket #needed for socket.timeout exception


if(len(sys.argv)!=3):
	print("usage: " + sys.argv[0] + " <IP> <DevID>")
	exit(1)

ip       = sys.argv[1]
devid    = sys.argv[2]

device   = pytuya.OutletDevice(devid,ip,"")

data = 0 #stub for the try except
try:
	data = device.status()
except (ConnectionResetError, socket.timeout, OSError)  as e:
	print("A problem occur please retry...")
	exit(1)

print("\nPlug State Information:")
print(data)

print("\nPlug DPS List:")

dps_list = ""
first=True
for key in data['dps'].keys():
	
	if(type (data['dps'][key]) is bool):
		if(not first):
			dps_list += ";"
		dps_list += str(int(key))
		first=False
				
print(dps_list)
