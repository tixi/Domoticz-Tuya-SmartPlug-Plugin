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

"""
<plugin key="tixi_tuya_smartplug_plugin" name="Tuya SmartPlug" author="tixi" version="2.0.2" externallink=" https://github.com/tixi/Domoticz-Tuya-SmartPlug-Plugin">
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

class BasePlugin:
	
	__HB_BASE_FREQ        = 2
	__VALID_CMD           = ('status','On','Off')

	def __init__(self):
		self.__address      = None          		#IP address of the smartplug
		self.__devID        = None          		#devID of the smartplug
		self.__localKey     = None          		#localKey of the smartplug
		self.__device       = None          		#pytuya object of the smartplug
		self.__runAgain     = self.__HB_BASE_FREQ	#heartbeat frequency (20 seconds)
		self.__connection   = None					#connection to the tuya plug
		self.__last_cmd	    = None          		#last command (None/'On'/'Off'/'status')
		self.__last_unit	= None					#last unit for the command
		self.__dps_units    = None					#list of dps for multiplug
		
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
		
		
		self.__dps_units = []
		for val in Parameters["Mode3"].split(";"):
			self.__dps_units.append(int(val))
		#Domoticz.Debug(str(self.__dps_units))
		
		#initialize the defined device in Domoticz
		#if (len(Devices) == 0):
		#	Domoticz.Device(Name="Tuya SmartPlug", Unit=self.__UNIT, TypeName="Switch").Create()
		#	Domoticz.Log("Tuya SmartPlug Device created.")
		
		if(len(Devices) < len(self.__dps_units)):
			for val in self.__dps_units:
				Domoticz.Device(Name="Tuya SmartPlug #" + str(val), Unit=val, TypeName="Switch").Create()
				Domoticz.Log("Tuya SmartPlug Device #" + str(val) +" created.")
		
		#create the pytuya object
		self.__device = pytuya.OutletDevice(self.__devID, self.__address, self.__localKey)

		#start the connection
		self.__last_cmd = 'status'
		self.__connection = Domoticz.Connection(Name="Tuya", Transport="TCP/IP", Address=self.__address, Port="6668")
		self.__connection.Connect()

	def onConnect(self, Connection, Status, Description):
		if (Connection == self.__connection):
			if (Status == 0):
				Domoticz.Debug("Connected successfully to: "+Connection.Address+":"+Connection.Port)
				if(self.__last_cmd != None):
					self.__command_to_execute(self.__last_cmd,self.__last_unit)
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
			#return (False,result['dps'][self.__DPS_ID])
			return (False,result['dps'])
		except (JSONError, KeyError) as e:
			return (True,"")

	def onMessage(self, Connection, Data):
		Domoticz.Debug("onMessage called: " + Connection.Address + ":" + Connection.Port +" "+ str(Data))
		
		if (Connection == self.__connection):
			
			if(self.__last_cmd == None):#skip nothing was waiting
				return
			
			(error,state) = self.__extract_status(Data)
			if(error):
				self.__command_to_execute(self.__last_cmd,self.__last_unit)
				return

			if(self.__last_cmd == 'status'):
				self.__last_cmd = None
			
			for val in self.__dps_units:
				if(state[str(val)]):
					UpdateDevice(val, 1, "On")
					if(self.__last_cmd == 'On' and self.__last_unit == val):
						self.__last_cmd  = None
						self.__last_unit = None
				else:
					UpdateDevice(val, 0, "Off")
					if(self.__last_cmd == 'Off' and self.__last_unit == val):
						self.__last_cmd  = None
						self.__last_unit = None
						
				
			#if(state[str(self.__UNIT)]):
			#	UpdateDevice(self.__UNIT, 1, "On")
			#	if(self.__last_cmd == 'On'):
			#		self.__last_cmd = None						
			#else:
			#	UpdateDevice(self.__UNIT, 0, "Off")
			#	if(self.__last_cmd == 'Off'):
			#		self.__last_cmd = None

			if(self.__last_cmd != None):
				self.__command_to_execute(self.__last_cmd,self.__last_unit)

	def __command_to_execute(self,Command,Unit):
		
		if(Command not in self.__VALID_CMD):
			Domoticz.Error("Undefined command: " + Command)
			return
		
		if(Command == 'status'):
			if(self.__last_cmd == None):
				self.__last_cmd = Command
		else:#On/Off
			self.__last_cmd  = Command
			self.__last_unit = Unit
 		
		if(self.__connection.Connected()):
			if(Command == 'On'):
				if(Unit==None):
					Domoticz.Debug("Unit=None for On command")
				else:
					payload = self.__device.generate_payload('set', {str(Unit):True})
					self.__connection.Send(payload)
					status_request = True
			elif(Command == 'Off'):
				if(Unit==None):
					Domoticz.Debug("Unit=None for Off command")
				else:
					payload = self.__device.generate_payload('set', {str(Unit):False})
					self.__connection.Send(payload)
					status_request = True
			else: #(Command == 'status')
				status_request = True
		
			if(status_request):
				payload=self.__device.generate_payload('status')
				self.__connection.Send(payload)
		else:
			self.__connection.Connect()

	def onCommand(self, Unit, Command, Level, Hue):
		Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command))
		self.__command_to_execute(Command,Unit)
		

	def onDisconnect(self, Connection):
		Domoticz.Debug("Disconnected from: "+Connection.Address+":"+Connection.Port)

	def onHeartbeat(self):
		self.__runAgain -= 1
		if(self.__runAgain == 0):
			self.__runAgain = self.__HB_BASE_FREQ				
			self.__command_to_execute('status',None)
	
	#onStop Domoticz function
	def onStop(self):
		self.__device     = None
		self.__last_cmd   = None
		self.__last_unit  = None
		if(self.__connection.Connected()):
			self.__connection.Disconnect()
		self.__connection = None

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
