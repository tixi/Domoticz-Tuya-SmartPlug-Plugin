########################################################################################
# 	Domoticz Tuya Smart Plug Python Plugin                                       	   #
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
<plugin key="sincze_tuya_smartplug_plugin" name="Tuya SmartPlug Config" author="tixi_sincze" version="1.0.0" externallink=" https://github.com/sincze/Domoticz-Tuya-SmartPlug-Plugin">
	<params>
		<param field="Address" label="IP address" width="200px" required="true"/>
		<param field="Mode1" label="DevID" width="200px" required="true"/>
		<param field="Mode2" label="Local Key" width="200px" required="true"/>
		<param field="Mode3" label="DPS" width="200px" required="true" default="1"/>
		<param field="Mode4" label="DPS group" width="200px" required="true" default="None"/>
		<param field="Mode5" label="ID Amp;Watt;Volt" width="200px" required="true" default="4;5;6"/>
		<param field="Mode6" label="Debug" width="75px">
			<options>
				<option label="0"   value="0" default="true"/>
				<option label="1"   value="1"/>
				<option label="2"   value="2"/>
				<option label="4"   value="4"/>
				<option label="8"   value="8"/>
				<option label="16"  value="16"/>
				<option label="32"  value="32"/>
				<option label="64"  value="64"/>
				<option label="128" value="128"/>
			</options>
		</param>
	</params>
</plugin>
"""



# https://wiki.domoticz.com/wiki/Developing_a_Python_plugin
# Debugging
# Value 	Meaning
# 0 		None. All Python and framework debugging is disabled.
# 1 		All. Very verbose log from plugin framework and plugin debug messages.
# 2 		Mask value. Shows messages from Plugin Domoticz.Debug() calls only.
# 4 		Mask Value. Shows high level framework messages only about major the plugin.
# 8 		Mask Value. Shows plugin framework debug messages related to Devices objects.
# 16 		Mask Value. Shows plugin framework debug messages related to Connections objects.
# 32 		Mask Value. Shows plugin framework debug messages related to Images objects.
# 64 		Mask Value. Dumps contents of inbound and outbound data from Connection objects.
# 128 		Mask Value. Shows plugin framework debug messages related to the message queue. 

import Domoticz
import pytuya
import json

########################################################################################
#
# plug object (represents a socket of the Tuya device)
#
########################################################################################
class Plug:

	#######################################################################
	#
	# constructor
	#
	#######################################################################
	def __init__(self,unit):
		self.__dps_id   = unit		# dps id
		self.__command  = None		# command ('On'/'Off'/None)
		self.__alwaysON = False		# True if the socket should be always ON, False otherwise
		return
	
	#######################################################################
	# update_state function
	#		update the domoticz device 
	#		and checks if the last command is equal to the current state
	#
	# parameters:
	#		state: True <=> On ; False <=> Off
	#
	# returns: 
	#		True in case of an error (the state does not correspond to the command)
	#		False otherwise
	#######################################################################
	def update_state(self,state): #state: True <=> On ; False <=> Off
		
		if(state):
			UpdateDevice(self.__dps_id, 1, "On")
			if(self.__command == 'Off'):
				return True
			else:
				self.__command = None
		
		elif(self.__alwaysON): #if not state: need to change the state for always_on devices
			self.__command = 'On'
			return True
			
		else:
			UpdateDevice(self.__dps_id, 0, "Off")
			if(self.__command == 'On'):
				return True
			else:
				self.__command = None

		return False
	
	#######################################################################
	#
	# set_command function
	# 		set the command for the next request
	#
	#######################################################################
	def set_command(self,cmd):
		if(self.__alwaysON):
			self.__command = 'On'
		else:
			self.__command = cmd
	
	#######################################################################
	#
	# set_alwaysON function
	# 		set __alwaysON to True
	#
	#######################################################################
	def set_alwaysON(self):
		self.__alwaysON = True
		self.__command  = 'On'
	
	#######################################################################
	#
	# put_payload function
	#		add to dict_payload the command to be sent to the device
	#
	#######################################################################
	def put_payload(self,dict_payload):
		
		if(self.__command == None):
			return
		
		if(self.__command =="On"):
			dict_payload[str(self.__dps_id)] = True
		else:
			dict_payload[str(self.__dps_id)] = False

########################################################################################
	
########################################################################################
#
# plugin object
#
########################################################################################
class BasePlugin:
	
	#######################################################################
	#
	# constant definition
	#
	#######################################################################
	__HB_BASE_FREQ = 2			  #heartbeat frequency (val x 10 seconds)
	__VALID_CMD    = ('On','Off') #list of valid command

	#######################################################################
	#
	# private functions definition
	#	__extract_status
	#	__is_encoded
	#	__command_to_execute
	#
	#######################################################################
	
	
	#######################################################################
	#
	# __extract_status
	#
	# Parameter
	#	Data: a received payload from the tuya smart plug
	#
	# Returns a tuple (bool,dict)
	#	first:  set to True if an error occur and False otherwise
	#	second: dict of the dps (irrelevant if first is True )
	#
	#######################################################################
	def __extract_status(self, Data):

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


	#######################################################################
	#
	# __is_encoded
	#
	# Parameter
	#	Data: a received payload from the tuya smart plug
	#
	# Returns 
	#	True if Data is encoded
	#	False otherwise
	#
	# Remark: for debugging purpose
	#
	#######################################################################
	#~ def __is_encoded(self, Data):

		#~ tmp = Data[20:-8]  # hard coded offsets
		#~ if(tmp.startswith(b'3.1')):#PROTOCOL_VERSION_BYTES
			#~ return True
		#~ else:
			#~ return False
			
	#######################################################################
	#
	# __command_to_execute
	#	send a command (set or status) to the tuya device
	#
	#
	#######################################################################
	def __command_to_execute(self):
		
		self.__runAgain = self.__HB_BASE_FREQ
				
		if(self.__connection.Connected()):
					
			dict_payload = {}
			
			for key in self.__plugs:
				self.__plugs[key].put_payload(dict_payload)
			
			if(len(dict_payload) != 0):
				self.__state_machine = 1
				payload = self.__device.generate_payload('set', dict_payload)
				self.__connection.Send(payload)
			
			else:
				self.__state_machine = 2
				payload=self.__device.generate_payload('status')
				self.__connection.Send(payload)	
			
		else:
			if(not self.__connection.Connecting()):
				self.__connection.Connect()	
	
	#######################################################################
	#
	# constructor
	#
	#######################################################################
	def __init__(self):
		self.__address          = None          		#IP address of the smartplug
		self.__devID            = None          		#devID of the smartplug
		self.__localKey         = None          		#localKey of the smartplug
		self.__device           = None          		#pytuya object of the smartplug
		self.__ampere	        = None					#key for Ampere
		self.__watt             = None					#key for Watt
		self.__voltage          = None					#key for Voltage
		self.__runAgain         = self.__HB_BASE_FREQ	#heartbeat frequency
		self.__connection       = None					#connection to the tuya plug
		self.__unit2dps_id_list = None					#mapping between Unit and list of dps id
		self.__plugs	        = None					#mapping between dps id and a plug object
		self.__state_machine    = 0						#state_machine: 0 -> no waiting msg ; 1 -> set command sent ; 2 -> status command sent
		return
		
	#######################################################################
	#		
	# onStart Domoticz function
	#
	#######################################################################
	def onStart(self):
		
		# Debug mode
		Domoticz.Debugging(int(Parameters["Mode6"]))
		Domoticz.Debug("onStart called")
			
		#get parameters
		self.__address  = Parameters["Address"]
		self.__devID    = Parameters["Mode1"]
		self.__localKey = Parameters["Mode2"]
		self.__ampere, self.__watt, self.__voltage = Parameters["Mode5"].split(";")
		
		#set the next heartbeat
		self.__runAgain = self.__HB_BASE_FREQ
		
		#build internal maps (__unit2dps_id_list and __plugs)
		self.__unit2dps_id_list = {}
		self.__plugs            = {}
		max_unit                = 0
		max_dps					= 0
		for val in sorted(Parameters["Mode3"].split(";")):
			
			self.__unit2dps_id_list[int(val)]=[int(val),]
			
			self.__plugs[int(val)]=Plug(int(val))
			
			if(int(val)>max_unit):
				max_unit=int(val)
	
		max_dps = max_unit
		
		#groups management: #syntax: 1;2 : 3;4
		# +5 instead of +1 to have spare room for the extra devices for Amp, W, kWh
		max_unit = max_unit + 5
		if(Parameters["Mode4"]!="None"):
			groups = Parameters["Mode4"].split(":")
			for group in groups:
				self.__unit2dps_id_list[max_unit]=[]
				for val in sorted(group.split(";")):
					self.__unit2dps_id_list[max_unit].append(int(val))
				max_unit = max_unit + 1
				
		#create domoticz devices			
		if(len(Devices) == 0):
			for val in self.__unit2dps_id_list:
				
				if(val <= max_dps): #single socket dps
					Domoticz.Device(Name="Tuya SmartPlug (Switch)", Unit=val, TypeName="Switch").Create()
					Domoticz.Log("Tuya SmartPlug Device (Switch) #" + str(val) +" created.")
					## After the last DPS add the global devices
					if(val == max_dps):
						Domoticz.Device(Name="Tuya SmartPlug (A)" , Unit=val+1, TypeName="Current (Single)").Create()
						Domoticz.Log("Tuya SmartPlug Device (A) #" + str(val+1) +" created.")
						Domoticz.Device(Name="Tuya SmartPlug (kWh)", Unit=val+2, TypeName="kWh").Create()
						Domoticz.Log("Tuya SmartPlug Device kWh #" + str(val+2) +" created.")
						Domoticz.Device(Name="Tuya SmartPlug (V)", Unit=val+3, TypeName="Voltage").Create()
						Domoticz.Log("Tuya SmartPlug Device (V) #" + str(val+3) +" created.")
						Domoticz.Device(Name="Tuya SmartPlug (W)", Unit=val+4, TypeName="Usage").Create()
						Domoticz.Log("Tuya SmartPlug Device (W) #" + str(val+4) +" created.")

				else: #group: selector switch
					Options = {"LevelActions": "|",
						"LevelNames": "Off|On",
						"LevelOffHidden": "false",
						"SelectorStyle": "0"}
					Domoticz.Device(Name="Tuya SmartPlug #" + str(val), Unit=val, TypeName="Selector Switch", Options=Options).Create()
					Domoticz.Log("Tuya SmartPlug Device #" + str(val) +" created.")
		
		#manage always on
		#if(Parameters["Mode5"]!="None"):
		#	for val in sorted(Parameters["Mode5"].split(";")):
		#		self.__plugs[int(val)].set_alwaysON()
		
		#create the pytuya object
		self.__device = pytuya.OutletDevice(self.__devID, self.__address, self.__localKey)

		#state machine
		self.__state_machine = 0

		#start the connection
		self.__connection = Domoticz.Connection(Name="Tuya", Transport="TCP/IP", Address=self.__address, Port="6668")
		self.__connection.Connect()

	#######################################################################
	#		
	# onConnect Domoticz function
	#
	#######################################################################
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
				


	#######################################################################
	#		
	# onMessage Domoticz function
	#
	#######################################################################
	def onMessage(self, Connection, Data):
		Domoticz.Debug("onMessage called: " + Connection.Address + ":" + Connection.Port +" "+ str(Data))
		
		if (Connection == self.__connection):
			
			if(self.__state_machine == 0):#skip nothing was waiting
				return
			
			if(self.__state_machine == 1):#after a set command: need to ask the status
				self.__state_machine = 2
				payload=self.__device.generate_payload('status')
				self.__connection.Send(payload)#TODO active connection check (it should be because we just get a message)
				return
				
			#now self.__state_machine == 2
			self.__state_machine = 0
			
			(error,state) = self.__extract_status(Data)
			if(error):
				self.__command_to_execute()
				return
						
			error = False
			for key in self.__plugs:				
				error = error or self.__plugs[key].update_state(state[str(key)])	
				Devices[key+1].Update(0,str(state[str(self.__ampere)]/1000))	# TypeName="Current (Single)
				Devices[key+2].Update(0,str(state[str(self.__watt)]/10) + ";0")	# kWh / Calculated
				Devices[key+3].Update(0,str(state[str(self.__voltage)]/10)) 	# TypeName="Voltage"
				Devices[key+4].Update(0,str(state[str(self.__watt)]/10)) 		# TypeName="Usage"
				
				Domoticz.Debug("Updated: " + str(state[str(self.__ampere)]/1000) + " Ampere Key is:" + str(key+1))
				Domoticz.Debug("Updated: " + str(state[str(self.__watt)]/10) + " Watt Key is:" + str(key+12))
				Domoticz.Debug("Updated: " + str(state[str(self.__voltage)]/10) + " Voltage Key is:" + str(key+13))
			
			if(error):
				self.__command_to_execute()

	#######################################################################
	#		
	# onCommand Domoticz function
	#
	#######################################################################
	def onCommand(self, Unit, Command, Level, Hue):
		Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + " Level: " + str(Level))
		
		if(Command=="Set Level"): #group (selector switch): convert level to command (0 <=> 'Off' ; 10 <=> 'On')
			if(Level==0):
				Command = 'Off'
			elif(Level==10):
				Command = 'On'
			else:
				Domoticz.Error("Undefined Level: " + str(Level))
				return
			
		if(Command not in self.__VALID_CMD):
			Domoticz.Error("Undefined command: " + Command)
			return
		
		for val in self.__unit2dps_id_list[Unit]:
			self.__plugs[val].set_command(Command)
		
		self.__command_to_execute()		

	#######################################################################
	#		
	# onDisconnect Domoticz function
	#
	#######################################################################
	def onDisconnect(self, Connection):
		Domoticz.Debug("Disconnected from: "+Connection.Address+":"+Connection.Port)

	#######################################################################
	#		
	# onHeartbeat Domoticz function
	#
	#######################################################################
	def onHeartbeat(self):
		self.__runAgain -= 1
		if(self.__runAgain == 0):
			self.__command_to_execute()
	
	#######################################################################
	#		
	# onStop Domoticz function
	#
	#######################################################################
	def onStop(self):
		self.__device           = None
		self.__plugs	        = None
		self.__unit2dps_id_list = None
		if(self.__connection.Connected() or self.__connection.Connecting()):
			self.__connection.Disconnect()
		self.__connection       = None
		self.__state_machine    = 0

########################################################################################
#
# Domoticz plugin management
#
########################################################################################
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
