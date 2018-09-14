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
<plugin key="tixi_tuya_smartplug_plugin" name="Tuya SmartPlug" author="tixi" version="1.0.0" externallink=" https://github.com/tixi/Domoticz-Tuya-SmartPlug-Plugin">
	<params>
		<param field="Address" label="IP address" width="200px" required="true"/>
		<param field="Mode1" label="DevID" width="200px" required="true"/>
		<param field="Mode2" label="Local Key" width="200px" required="true"/>
		<param field="Mode3" label="Replay" width="75px">
			<options>
				<option label="Yes" value="Yes" default="true"/>
				<option label="No" value="No" />
			</options>
		</param>
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
import socket #needed for socket.timeout exception
import pytuya

class BasePlugin:

	__UNIT = 1
	__MINUTE = 6 #heartbeat is called every 10 seconds and executed every 60 seconds

	def __init__(self):
		self.__address             = None          #ip address of the smartplug
		self.__devID               = None          #devID of the smartplug
		self.__localKey            = None          #localKey of the smartplug
		self.__device              = None          #pytuya object of the smartplug
		self.__replay              = True          #replay mode
		self.__last_cmd_for_replay = None          #last command for replay (None/"On"/"Off")
		self.__runAgain            = self.__MINUTE #heartbeat frequency
		return

	#check the current status (on/off) of the smartplug to update the device in Domoticz if needed
	def check_status(self):
		try:
			data = self.__device.status()
			if(data['dps']['1']):
				UpdateDevice(self.__UNIT, 1, "On")
			else:
				UpdateDevice(self.__UNIT, 0, "Off")
		except (ConnectionRefusedError, ConnectionResetError):
			Domoticz.Log("A problem occurs while connecting to the Smart Plug")
			Domoticz.Debug("Check if the Tuya app is closed on your smartphone")
			#if you observe this message only few times in debug logs it works correctly
			self.__runAgain = 0
		except (socket.timeout, OSError):
			Domoticz.Log("Smart Plug not reachable")
			Domoticz.Debug("Check if the Smart Plug is connected to the same wifi network")

	#execute a command
	def exec_cmd(self,Command):
		
		if(self.__replay):
			self.__last_cmd_for_replay=Command
		try:
			if (Command == 'On'):
				self.__device.turn_on()
				UpdateDevice(self.__UNIT, 1, "On")
			else: #Command=='Off'
				self.__device.turn_off()
				UpdateDevice(self.__UNIT, 0, "Off")
				
			self.__last_cmd_for_replay = None #if no exception no need for replay
			
		except (ConnectionRefusedError, ConnectionResetError):
			Domoticz.Log("A problem occurs while connecting to the Smart Plug")
			Domoticz.Debug("Check if the Tuya app is closed on your smartphone")
			#if you observe this message only few times in debug logs it works correctly (replay while fix it)
			
			if(self.__replay):
				Domoticz.Debug("Command for replay: " + Command)
			
		except (socket.timeout, OSError):
			Domoticz.Log("Smart Plug not reachable")
			Domoticz.Debug("Check if the Smart Plug is connected to the same wifi network")
			self.__last_cmd_for_replay = None #no replay if the smartplug is not connected

	#onStart Domoticz function
	def onStart(self):
		Domoticz.Debug("onStart called")
		# Debug mode
		if Parameters["Mode6"] == "Debug":
			Domoticz.Debugging(1)
		else:
			Domoticz.Debugging(0)
			
		#get parameters
		self.__address = Parameters["Address"]
		self.__devID = Parameters["Mode1"]
		self.__localKey = Parameters["Mode2"]
		
		if(Parameters["Mode3"]=="No"):
			self.__replay=False
			Domoticz.Log("Replay mode not activated")
			
		#initialize the defined device in Domoticz
		if (len(Devices) == 0):
			Domoticz.Device(Name="Tuya SmartPlug", Unit=self.__UNIT, TypeName="Switch").Create()
			Domoticz.Log("Tuya SmartPlug Device created.")
		
		#create the pytuya object to communicate with the smartplug 
		self.__device = pytuya.OutletDevice(self.__devID, self.__address, self.__localKey)

		#set the status
		self.check_status()

	#onCommand Domoticz function
	def onCommand(self, Unit, Command, Level, Hue):
		Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
		self.exec_cmd(Command)
		
	#onHeartbeat Domoticz function							
	def onHeartbeat(self):
		Domoticz.Debug("onHeartbeat called")
		
		if(self.__last_cmd_for_replay != None):#replay
			Domoticz.Debug("Replay: " + self.__last_cmd_for_replay)			
			self.exec_cmd(self.__last_cmd_for_replay)

		else:#normal case
			self.__runAgain -= 1
			if self.__runAgain == 0:
				self.__runAgain = self.__MINUTE
				self.check_status()

global _plugin
_plugin = BasePlugin()

def onStart():
	global _plugin
	_plugin.onStart()

def onCommand(Unit, Command, Level, Hue):
	global _plugin
	_plugin.onCommand(Unit, Command, Level, Hue)

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
