########################################################################################
# 	Domoticz Tuya Smart Plug Python Plugin                                       #
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

#<param field="Mode4" label="DPS group" width="200px" required="true" default="None"/>


"""
<plugin key="tixi_tuya_smartplug_plugin" name="Tuya SmartPlug" author="tixi" version="3.0.0" externallink=" https://github.com/tixi/Domoticz-Tuya-SmartPlug-Plugin">
	<params>
		<param field="Address" label="IP address" width="200px" required="true"/>
		<param field="Mode1" label="DevID" width="200px" required="true"/>
		<param field="Mode2" label="Local Key" width="200px" required="true"/>
		<param field="Mode3" label="DPS" width="200px" required="true" default="1"/>
		<param field="Mode6" label="Debug" width="75px">
			<options>
				<option label="True" value="Debug"/>
				<option label="False" value="Normal" default="true"/>
			</options>
		</param>
	</params>
</plugin>
"""

import Domoticz
import pytuya
import json


class Plug:
	
	def __init__(self,unit):
		self.__dps_id       = unit
		self.__command = None
		return
	
	#returns True in case the state does not correspond to the command
	# 		 False otherwise
	def update_state(self,state): #state: True <=> On ; False <=> Off
		
		if(state):
			UpdateDevice(self.__dps_id, 1, "On")
			if(self.__command == 'Off'):
				return True
			else:
				self.__command = None
				
		else:
			UpdateDevice(self.__dps_id, 0, "Off")
			if(self.__command == 'On'):
				return True
			else:
				self.__command = None

		return False
	
	#set the command to perform a request
	def set_command(self,cmd):
		self.__command = cmd
	
	#put the payload in dict_payload for the plug
	def put_payload(self,dict_payload):
		
		if(self.__command == None):
			return
		
		if(self.__command =="On"):
			dict_payload[str(self.__dps_id)] = True
		else:
			dict_payload[str(self.__dps_id)] = False
			

class BasePlugin:
	
	__HB_BASE_FREQ        = 2
	__VALID_CMD           = ('On','Off')

	def __init__(self):
		self.__address          = None          		#IP address of the smartplug
		self.__devID            = None          		#devID of the smartplug
		self.__localKey         = None          		#localKey of the smartplug
		self.__device           = None          		#pytuya object of the smartplug
		self.__runAgain         = self.__HB_BASE_FREQ	#heartbeat frequency (20 seconds)
		self.__connection       = None					#connection to the tuya plug
		self.__unit2dps_id_list = None					#mapping between Unit and list of dps id
		self.__plugs	        = None					#list of plugs (internal representation)
		self.__request_pending  = False					#True if a request was sent
		
		return
		
	#onStart Domoticz function
	def onStart(self):
		
		# Debug mode
		if(Parameters["Mode6"] == "Debug"):
			Domoticz.Debugging(1)
			Domoticz.Debug("onStart called")
		else:
			Domoticz.Debugging(0)
			
		#get parameters
		self.__address  = Parameters["Address"]
		self.__devID    = Parameters["Mode1"]
		self.__localKey = Parameters["Mode2"]
		
		
		self.__unit2dps_id_list = {}
		self.__plugs            = {}
		max_unit                = 0
		for val in sorted(Parameters["Mode3"].split(";")):
			
			self.__unit2dps_id_list[int(val)]=[int(val),]
			
			self.__plugs[int(val)]=Plug(int(val))
			
			if(int(val)>max_unit):
				max_unit=int(val)
		#Domoticz.Error(str(self.__unit2dps_id_list))
		
		#groups management: not ready yet
		#max_unit = max_unit + 1
		#if(Parameters["Mode4"]!="None"):
		#	groups = Parameters["Mode4"].split(":")
		#	for group in groups:
		#		self.__unit2dps_id_list[max_unit]=[]
		#		for val in sorted(group.split(";")):
		#			self.__unit2dps_id_list[max_unit].append(int(val))
		#		max_unit = max_unit + 1
				
						
		if(len(Devices) == 0):
			for val in self.__unit2dps_id_list:
				Domoticz.Device(Name="Tuya SmartPlug #" + str(val), Unit=val, TypeName="Switch").Create()
				Domoticz.Log("Tuya SmartPlug Device #" + str(val) +" created.")
		
		#create the pytuya object
		self.__device = pytuya.OutletDevice(self.__devID, self.__address, self.__localKey)

		#start the connection
		self.__connection = Domoticz.Connection(Name="Tuya", Transport="TCP/IP", Address=self.__address, Port="6668")
		self.__connection.Connect()

	def onConnect(self, Connection, Status, Description):
		if (Connection == self.__connection):
			if (Status == 0):
				Domoticz.Debug("Connected successfully to: "+Connection.Address+":"+Connection.Port)
				self.__command_to_execute()
			else:
				Domoticz.Debug("OnConnect Error Status: " + str(Status))
				if(Status==113):#no route to host error (skip to avoid intempestive connect call)
					return
				if(self.__connection.Connected()):
					self.__connection.Disconnect()
				if(not self.__connection.Connecting()):
					self.__connection.Connect()
				
	def __extract_status(self, Data):
		""" Returns a tuple (bool,dict) 
			first:  set to True if an error occur and False otherwise
			second: dict of the dps
			
			second is irrelevant if first is True 
		"""
		start=Data.find(b'{"devId')
		
		if(start==-1):
			return (True,"")
			
		result = Data[start:] #in 2 steps to deal with the case where '}}' is present before {"devId'
			
		end=result.find(b'}}')
		
		if(end==-1):
			return (True,"")
		
		end=end+2
		result = result[:end]
		if not isinstance(result, str):
			result = result.decode()
			
		try:
			result = json.loads(result)
			return (False,result['dps'])
		except (JSONError, KeyError) as e:
			return (True,"")


	def onMessage(self, Connection, Data):
		Domoticz.Debug("onMessage called: " + Connection.Address + ":" + Connection.Port +" "+ str(Data))
		
		if (Connection == self.__connection):
			
			if(not self.__request_pending):#skip nothing was waiting
				return
			
			self.__request_pending = False
			
			(error,state) = self.__extract_status(Data)
			if(error):
				self.__command_to_execute()
				return
			
			
			error = False
			for key in self.__plugs:				
				error = error or self.__plugs[key].update_state(state[str(key)])	
				
			if(error):
				self.__command_to_execute()


	def __command_to_execute(self):
				
		if(self.__connection.Connected()):
			
			self.__request_pending = True
			
			dict_payload = {}
			
			for key in self.__plugs:
				self.__plugs[key].put_payload(dict_payload)
			
			if(len(dict_payload) != 0):
				payload = self.__device.generate_payload('set', dict_payload)
				self.__connection.Send(payload)
				
			payload=self.__device.generate_payload('status')
			self.__connection.Send(payload)	
			
		else:
			if(not self.__connection.Connecting()):
				self.__connection.Connect()


	def onCommand(self, Unit, Command, Level, Hue):
		Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command))
		
		if(Command not in self.__VALID_CMD):
			Domoticz.Error("Undefined command: " + Command)
			return
		
		for val in self.__unit2dps_id_list[Unit]:
			self.__plugs[val].set_command(Command)
		
		self.__command_to_execute()
		

	def onDisconnect(self, Connection):
		Domoticz.Debug("Disconnected from: "+Connection.Address+":"+Connection.Port)

	def onHeartbeat(self):
		self.__runAgain -= 1
		if(self.__runAgain == 0):
			self.__runAgain = self.__HB_BASE_FREQ				
			self.__command_to_execute() #only a status request should be sent
	
	#onStop Domoticz function
	def onStop(self):
		self.__device          = None
		self.__plugs	       = None
		if(self.__connection.Connected() or self.__connection.Connecting()):
			self.__connection.Disconnect()
		self.__connection      = None
		self.__request_pending = False

global _plugin
_plugin = BasePlugin()

def onStart():
	global _plugin
	_plugin.onStart()

def onStop():
	global _plugin
	_plugin.onStop()

def onConnect(Connection, Status, Description):
	global _plugin
	_plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
	global _plugin
	_plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
	global _plugin
	_plugin.onCommand(Unit, Command, Level, Hue)

def onDisconnect(Connection):
	global _plugin
	_plugin.onDisconnect(Connection)

def onHeartbeat():
	global _plugin
	_plugin.onHeartbeat()

################################################################################
# Generic helper functions
################################################################################

def UpdateDevice(Unit, nValue, sValue, TimedOut=0, AlwaysUpdate=False):
	# Make sure that the Domoticz device still exists (they can be deleted) before updating it
	if Unit in Devices:
		if Devices[Unit].nValue != nValue or Devices[Unit].sValue != sValue or Devices[Unit].TimedOut != TimedOut or AlwaysUpdate:
			Devices[Unit].Update(nValue=nValue, sValue=str(sValue), TimedOut=TimedOut)
			Domoticz.Debug("Update " + Devices[Unit].Name + ": " + str(nValue) + " - '" + str(sValue) + "'")
