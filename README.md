NOTE I'm no longer using these devices so this is not actively maintained.

# Domoticz-Tuya-SmartPlug-Plugin

A Domoticz plugin to manage Tuya Smart Plug (single and multi socket device)
This is a modified plugin from the modified plugion by sincze, The sincze plugin used a script called by cron and the plugin just created the devices.
Now all is managed by the plugin and using the tinytuya API (the pituya was obsolete and no longer supported).

![devices](https://github.com/sincze/Domoticz-Tuya-SmartPlug-Plugin/blob/master/Tuya%20Smartplug.JPG)

Multi socket has not been tested. I only have 1 socket. Keep in mind I am not a Python developer, pertinent remarks are appreciated. 
Plugin is provided on best-effort.

## ONLY TESTED FOR Raspberry Pi

With Python version 3.7.3 & Domoticz version V2022.1
## Prerequisites

This plugin is based on the tinytuya Python library. For the installation of this library,
follow the Installation guide below.
See [`https://github.com/jasonacox/tinytuya] for more information.

For the pyaes Python library, you need pyaes. pyaes can be installed with pip:
```
pip3 install pyaes
```
See [`https://pypi.org/project/pyaes/`] for more information.

## Installation

Assuming that domoticz directory is installed in your home directory.

```bash
cd ~/domoticz/plugins
git clone https://github.com/Tatroxitum/Domoticz-Tuya-SmartPlug-Plugin
cd Domoticz-Tuya-SmartPlug-Plugin
git clone https://github.com/clach04/python-tuya.git
pip3 show pytuya #show pytuya path
ln -s ~[pytuya path]/pytuya pytuya
python -m tinytuya scan #see under for devID & local key extraction
# restart domoticz:
sudo /etc/init.d/domoticz.sh restart
```
## Known issues

If the watt values are very low (for example 3W) there is an issue in Domoticz and the values in kwh are not calculated
https://github.com/domoticz/domoticz/issues/5326


## Updating

Like other plugins, in the Domoticz-Tuya-SmartPlug-Plugin directory:
```bash
git pull
sudo /etc/init.d/domoticz.sh restart
```

## Parameters

| Parameter | Value |
| :--- | :--- |
| **IP address** | IP of the Smart Plug eg. 192.168.1.231 |
| **DevID** | devID of the Smart Plug |
| **Local Key** | Local Key of the Smart Plug |
| **DPS** |	1 for single socket device and a list of dps separated by ';' for multisocket device eg. 1;2;3;7 #not tested
| **DPS group** | None for single socket device and a list of list of dps separated by ':' for multisocket device eg. 1;2 : 3;7 #not tested
| **ID Amp;Watt;Volt** | Enter the ID's of these specific devices separated by ; eg 18;19;20 (nt tested with Multisocket)
| **Debug** | default is 0 |

**DPS** should only includes values that correspond to plug's dps id. Be careful some devices also have timers in the dps state.

**DPS group** can be used to group multiple sockets in one Domoticz switch.

Helper scripts get_dps.py turnON.py and turnOFF.py can help:
* to determine the dps list
* to check that the needed information are valid (i.e. devID and Local Key) before using the plugin.

## DevID & Local Key Extraction

Recommanded method:
Linking a Tuya device with Smart Link steps 1 to 3 then Listing Tuya devices from the Tuya Smart or Smart Life apps 1 to 3. 
Other steps are not mandatory.
[`https://github.com/codetheweb/tuyapi/blob/master/docs/SETUP.md#listing-tuya-devices-from-the-tuya-smart-or-smart-life-apps]

TinyTuya has a built in network scanner that can be used to find Tuya Devices on your local network. It will show Address, Device ID and Version for each device.
python -m tinytuya scan

## Acknowledgements

* Special thanks for all the hard work of [clach04](https://github.com/clach04), [codetheweb](https://github.com/codetheweb/) and all the other contributers on [python-tuya](https://github.com/clach04/python-tuya) and [tuyapi](https://github.com/codetheweb/tuyapi) who have made communicating to Tuya devices possible with open source code.
* Domoticz team
* Original Plugin by [Tixi](https://github.com/tixi/Domoticz-Tuya-SmartPlug-Plugin)
* Modifed Plugin by [sincze](https://github.com/sincze/Domoticz-Tuya-SmartPlug-Plugin)
