########################################################################################
# 	Domoticz Tuya Smart Plug Python Plugin                                       	   #
#                                                                                      #
# 	MIT License                                                                        #
#                                                                                      #
#	Copyright (c) 2018 tixi 
#	Modified (C) 2022 Tatroxitum : Updated to tinytuya interface and minor corrections #
#	Modified (C) 2022 Tatroxitum : Catch exception KeyError on update + change heartbeat#
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
<plugin key="sincze_tuya_smartplug_plugin" name="Tuya SmartPlug Config" author="tixi_sincze_tatroxitum" version="2.0.1" externallink=" https://github.com/sincze/Domoticz-Tuya-SmartPlug-Plugin">
	<params>
		<param field="Address" label="IP address" width="200px" required="true"/>
		<param field="Mode1" label="DevID" width="200px" required="true"/>
		<param field="Mode2" label="Local Key" width="200px" required="true"/>
		<param field="Mode3" label="DPS" width="200px" required="true" default="1"/>
		<param field="Mode4" label="DPS group" width="200px" required="true" default="None"/>
		<param field="Mode5" label="ID Amp;Watt;Volt" width="200px" required="true" default="18;19;20"/>
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
import tinytuya
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
		Domoticz.Debug("update_state begin")
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
		Domoticz.Debug("update_state end")
	
	#######################################################################
	#
	# set_command function
	# 		set the command for the next request
	#
	#######################################################################
	def set_command(self,cmd):
		Domoticz.Debug("set_command begin")
		if(self.__alwaysON):
			self.__command = 'On'
		else:
			self.__command = cmd
		Domoticz.Debug("set_command end")
		
	#######################################################################
	#
	# set_alwaysON function
	# 		set __alwaysON to True
	#
	#######################################################################
	def set_alwaysON(self):
		Domoticz.Debug("set_alwaysON begin")
		self.__alwaysON = True
		self.__command  = 'On'
		Domoticz.Debug("set_alwaysON end")
		
	#######################################################################
	#
	# put_payload function
	#		add to dict_payload the command to be sent to the device
	#
	#######################################################################
	def put_payload(self,dict_payload):
		Domoticz.Debug("put_payload begin")
		if(self.__command == None):
			return
		
		if(self.__command =="On"):
			dict_payload[str(self.__dps_id)] = True
		else:
			dict_payload[str(self.__dps_id)] = False
		Domoticz.Debug("put_payload end")
		
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
	__HB_BASE_FREQ = 1			  #heartbeat frequency (val x 10 seconds)
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
		Domoticz.Debug("extract_status begin")
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
		Domoticz.Debug("extract_satus end")

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
	# UpdateFromPlug function
	#
	#######################################################################
	def UpdateFromPlug(self):
		Domoticz.Debug("UpdateFromPlug begin")
		
		if(self.__state_machine == 0):#skip nothing was waiting
			Domoticz.Debug("UpdateFromPlug self.__state_machine == 0")
			return
		
		if(self.__state_machine == 1):#after a set command: need to ask the status
			Domoticz.Debug("UpdateFromPlug self.__state_machine == 1")
			self.__state_machine = 2
			return
		
		if(self.__state_machine == 2): # update from plug asked
			self.__state_machine = 0
		
			Data = self.__device.status()
			Domoticz.Debug(str(Data))
			
			values = Data["dps"]
			try:
				switch_state = bool(Data['dps']["1"])
				ampere = int(values[self.__ampere])
				watt = int(values[self.__watt])
				voltage = int(values[self.__voltage])
		
				for key in self.__plugs:
					#Update Switch
					if(values["1"]==1):
						Domoticz.Debug("Switch updated to ON")
						self.__plugs[key].update_state(1)
					else:
						Domoticz.Debug("Switch updated to OFF")
						self.__plugs[key].update_state(0)
					#Update Ampere                
					if(ampere!=0):
						Devices[key+1].Update(0,str(ampere/1000)) # TypeName="Current (Single)
					else:
						Devices[key+1].Update(0,str("0"))
					#Update Watt
					if(watt!=0):
						Domoticz.Debug(str(Devices[key+2].Options))
						Devices[key+2].Update(0,str(watt/10) + ";0") # kWh / Calculated
						Devices[key+4].Update(0,str(watt/10)) # TypeName="Usage"
					else:
						Devices[key+2].Update(0,str("0") + ";0")
						Devices[key+4].Update(0,str("0"))
					#Update Volts
					if(voltage!=0):
						Devices[key+3].Update(0,str(voltage/10)) # TypeName="Voltage"
					else:
						Devices[key+3].Update(0,str("0"))
		
				Domoticz.Debug("Updated: " + str(ampere) + " Ampere Key is:" + str(key+1) + "id" + str(self.__ampere))
				Domoticz.Debug("Updated: " + str(watt) + " Watt Key is:" + str(key+4) + "id" + str(self.__watt))
				Domoticz.Debug("Updated: " + str(voltage) + " Voltage Key is:" + str(key+3) + "id" + str(self.__voltage))
			except KeyError:
				Domoticz.Debug("KeyError no data received")		
		Domoticz.Debug("UpdateFromPlug end")
		
	#######################################################################
	#
	# __command_to_execute
	#	send a command (set or status) to the tuya device
	#
	#
	#######################################################################
	def __command_to_execute(self):
		Domoticz.Debug("command_to_execute begin")
		self.__runAgain = self.__HB_BASE_FREQ #set the next heartbeat
		if(self.__connection.Connected()): #check if plug is connected
			if(self.__state_machine == 1): #Cmd switch received from Domoticz
				if(Devices[1].nValue == 1):#Cmd : turn off switch
					self.__device.turn_off()#turn off plug
					self.__plugs[1].update_state(0)#update Domoticz Switch Status
				else:
					self.__device.turn_on()#Cmd : turn off switch
					self.__plugs[1].update_state(1)#turn on plug
				self.__state_machine = 2#update Domoticz Switch Status
				self.UpdateFromPlug()#now force update to get back the switch State
				
			else: #update Domotciz data from plug
				self.__state_machine = 2
				self.UpdateFromPlug()
			
		else:
			#not connected to plug, redo the connection
			if(not self.__connection.Connecting()):
				self.__connection.Connect()	
		Domoticz.Debug("command_to_execute end")
		
	#######################################################################
	#
	# constructor
	#
	#######################################################################
	def __init__(self):
		self.__address			= None					#IP address of the smartplug
		self.__devID			= None					#devID of the smartplug
		self.__localKey			= None					#localKey of the smartplug
		self.__device			= None					#tinytuya object of the smartplug
		self.__ampere			= None					#key for Ampere
		self.__watt				= None					#key for Watt
		self.__voltage			= None					#key for Voltage
		self.__runAgain			= self.__HB_BASE_FREQ	#heartbeat frequency
		self.__connection		= None					#connection to the tuya plug
		self.__unit2dps_id_list	= None					#mapping between Unit and list of dps id
		self.__plugs			= None					#mapping between dps id and a plug object
		self.__state_machine	= 0						#state_machine: 0 -> no waiting msg ; 1 -> set command sent ; 2 -> status command sent
		return
		
	#######################################################################
	#		
	# onStart Domoticz function
	#
	#######################################################################
	def onStart(self):
		Domoticz.Debug("onStart")
		# Debug mode
		Domoticz.Debugging(int(Parameters["Mode6"]))
		Domoticz.Debug("onStart called")
		
		#get parameters
		self.__address  = Parameters["Address"]
		self.__devID    = Parameters["Mode1"]
		self.__localKey = Parameters["Mode2"]
		self.__ampere, self.__watt, self.__voltage = Parameters["Mode5"].split(";")
		
		#set the next heartbeat to now to update data
		self.__runAgain = 1#set next heartbeat on start to update
		#state machine
		self.__state_machine = 2 #force first plug update
		
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
						Domoticz.Device(Name="Tuya SmartPlug (kWh)", Unit=val+2, TypeName="kWh", Options={"EnergyMeterMode":"1"}).Create() #kwh calculated by Domoticz as the device doesn't calculate it
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
		
		#create the tinytuya object
		self.__device = tinytuya.OutletDevice(self.__devID, self.__address, self.__localKey)
		self.__device.set_version(3.3)#force version to 3.3 (madnatory to work)
		
		#start the connection
		self.__connection = Domoticz.Connection(Name="Tuya", Transport="TCP/IP", Address=self.__address, Port="6668")
		self.__connection.Connect()

	#######################################################################
	#		
	# onConnect Domoticz function
	#
	#######################################################################
	def onConnect(self, Connection, Status, Description):
		Domoticz.Debug("onConnect")
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
		
		Domoticz.Debug("onConnect end")
		

	#######################################################################
	#		
	# onMessage Domoticz function
	#
	#######################################################################
	def onMessage(self, Connection, Data):
		Domoticz.Debug("onMessage called: " + Connection.Address + ":" + Connection.Port +" "+ str(Data))
		#method not used
	#	Domoticz.Debug("onMessage end")

	
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
				Domoticz.Debug("Set OnCommand Off")
			elif(Level==10):
				Command = 'On'
				Domoticz.Degug("Set OnCommand On")
			else:
				Domoticz.Error("Undefined Level: " + str(Level))
				return
			
		if(Command not in self.__VALID_CMD):
			Domoticz.Error("Undefined command: " + Command)
			return
		
		for val in self.__unit2dps_id_list[Unit]:
			self.__plugs[val].set_command(Command)
			Domoticz.Debug("Set OnCommand : "+ str(Command))
		self.__state_machine=1#force update of plug and Domoticz device
		self.__command_to_execute()		
		Domoticz.Debug("onCommand end")
		
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
		Domoticz.Debug("onHeartbeat")
		self.__runAgain -= 1
		if(self.__runAgain == 0):#time to update device
			self.__command_to_execute()
		Domoticz.Debug("onHeartbeat end")
	
	#######################################################################
	#		
	# onStop Domoticz function
	#
	#######################################################################
	def onStop(self):
		Domoticz.Debug("onStop")
		self.__device           = None
		self.__plugs	        = None
		self.__unit2dps_id_list = None
		if(self.__connection.Connected() or self.__connection.Connecting()):
			self.__connection.Disconnect()
		self.__connection       = None
		self.__state_machine    = 0
		Domoticz.Debug("onStop fin")
		
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
