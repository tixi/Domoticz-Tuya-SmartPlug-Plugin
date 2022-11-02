#!/usr/bin/python3

########################################################################################
#       Domoticz Tuya Smart Plug Python script                                         #
#                                                                                      #
#                                                                                      #
#                                                                                      #
#       Copyright (c) 2022 Wallb35                                                     #
#       Modified (c) 2022 Tatrocitum //add tinytuya API                                #
#                                                                                      #
#       Permission is hereby granted, free of charge, to any person obtaining a copy   #
#       of this software and associated documentation files (the "Software"), to deal  #
#       in the Software without restriction, including without limitation the rights   #
#       to use, copy, modify, merge, publish, distribute, sublicense, and/or sell      #
#       copies of the Software, and to permit persons to whom the Software is          #
#       furnished to do so, subject to the following conditions:                       #
#                                                                                      #
#       The above copyright notice and this permission notice shall be included in all #
#       copies or substantial portions of the Software.                                #
#                                                                                      #
#       THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR     #
#       IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,       #
#       FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE    #
#       AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER         #
#       LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,  #
#       OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE  #
#       SOFTWARE.                                                                      #
#                                                                                      #
########################################################################################

#v0.6 - 5 JUL 2022
#v1.0 - 01 NOV 2022

# Usage :
# get_dps.py <IP> <DevID> <DevKey> <butwatid> <butvolid> <butintid> <butkwhid>
# IP : device local IP 
# DEvID : Tuya device ID 
# DevKey : Tuya device local key ID
# butwatid : ID Domoticz du capteur virtuel utilisation électrique (W)
# butvolid : ID Domoticz du capteur virtuel tension (V)
# butintid : ID Domoticz du capteur virtuel ampere monophasé (A)
# butkwhid : ID Domoticz du capteur virtuel électrique instantané + compteur (modifié en mode compute) (kwh)

import sys
import tinytuya
import socket #needed for socket.timeout exception
import urllib.request
import base64

UPDATEOK = "success"
UPDATEFAILED = "FAILED"

DOMSERVER   = "xx.xx.xx.xx:xxxx" # domoticz local IP + port
DOMUSER = "xxxxxxx" # !!! domoticzuser
DOMPASS = "xxxxxxx" # !!! Domoticzpassword

BASE64STR = base64.encodebytes(('%s:%s' % (DOMUSER, DOMPASS)).encode()).decode().replace('\n', '')

def domrequest (url):
  request = urllib.request.Request(url)
  request.add_header("Authorization", "Basic %s" % BASE64STR)
  response = urllib.request.urlopen(request)
  return response.read()

if(len(sys.argv)!=8):
        print("usage: " + sys.argv[0] + " <IP> <DevID> <DevKey> <butwatid> <butvolid> <butintid> <butkwhid>")
        exit(1)

ip       = sys.argv[1]
devid    = sys.argv[2]
devkey   = sys.argv[3]
butwatid = sys.argv[4]
butvolid = sys.argv[5]
butintid = sys.argv[6]
butkwhid = sys.argv[7]

device   = tinytuya.OutletDevice(devid,ip,devkey)

data = 0 #stub for the try except
try:
        device.set_version(3.3) #Mandatory for setting plug version in tuya API
        data = device.status()
except (ConnectionResetError, socket.timeout, OSError)  as e:
        print("A problem occur please retry...")
        exit(1)

print("data : ",str(data)) #data received

values = data["dps"]
amp = int(values["18"])/1000
watt = int(values["19"])/10
volt= int(values["20"])/10

# Update instant Watt value
req = domrequest(
     DOMSERVER + "/json.htm?type=command&param=udevice&idx=" + butwatid + "&nvalue=0&svalue=" 
     + str(watt) 
    )

if "OK" in str(req):
     res = "OK"
else:
     res = "FAILED"

print("watts : domoticz update =>", (UPDATEOK if "OK" in str(req) else UPDATEFAILED), watt)

# Update instant+counter Watt value (Tuya device doesn't send it, it's the Domoticz counter that calculate it)   
req = domrequest(
     DOMSERVER + "/json.htm?type=command&param=udevice&idx=" + butkwhid + "&nvalue=0&svalue=" 
     + str(watt) + ";0"
    )

if "OK" in str(req):
     res = "OK"
else:
     res = "FAILED"

print("kwatts : domoticz update =>", (UPDATEOK if "OK" in str(req) else UPDATEFAILED), watt)

# Update instant Volt value
req = domrequest(
     DOMSERVER + "/json.htm?type=command&param=udevice&idx=" + butvolid + "&nvalue=0&svalue="
     + str(volt)
    )

if "OK" in str(req):
     res = "OK"
else:
     res = "FAILED"

print("volt : domoticz update =>", (UPDATEOK if "OK" in str(req) else UPDATEFAILED), volt)

# Update instant Ampere value
req = domrequest(
     DOMSERVER + "/json.htm?type=command&param=udevice&idx=" + butintid + "&nvalue=0&svalue="
     + str(amp)
    )

if "OK" in str(req):
     res = "OK"
else:
     res = "FAILED"

print("amp : domoticz update =>", (UPDATEOK if "OK" in str(req) else UPDATEFAILED), amp)