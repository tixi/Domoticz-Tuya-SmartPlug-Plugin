# Domoticz-Tuya-SmartPlug-Plugin

A Domoticz plugin to manage Tuya Smart Plug (single and multi socket device)

## ONLY TESTED FOR Raspberry Pi

With Python version 3.5 & Domoticz version 4.9700 (stable)
## Prerequisites

This plugin is based on the pytuya Python library. For the installation of this library,
follow the Installation guide below.
See [`https://github.com/clach04/python-tuya/`](https://github.com/clach04/python-tuya/) for more information.

For the pytuya Python library, you need pycrypto. pycrypto can be installed with pip:
```
pip3 install pycrypto
```
See [`https://pypi.org/project/pycrypto/`](https://pypi.org/project/pycrypto/) for more information.

## Installation

Assuming that domoticz directory is installed in your home directory.

```bash
cd ~/domoticz/plugins
git clone https://github.com/tixi/Domoticz-Tuya-SmartPlug-Plugin
cd Domoticz-Tuya-SmartPlug-Plugin
git clone https://github.com/clach04/python-tuya.git
ln -s ~/domoticz/plugins/Domoticz-Tuya-SmartPlug-Plugin/python-tuya/pytuya pytuya
# restart domoticz:
sudo /etc/init.d/domoticz.sh restart
```
In the web UI, navigate to the Hardware page. In the hardware dropdown there will be an entry called "Tuya SmartPlug".

## Known issues

1/ python environment

Domoticz may not have the path to the pycrypto library in its python environment.
In this case you will observe something starting like that in the log:
* failed to load 'plugin.py', Python Path used was 
* Module Import failed, exception: 'ImportError'

To find where pycrypto is installed, in a shell:
```bash
pip3 show pycrypto
```
The Crypto directory should be present in the directory indicated with Location.

when you have it, just add a symbolic link to it in Domoticz-Tuya-SmartPlug-Plugin directory with ```ln -s```.
Example:
```bash
cd ~/domoticz/plugins/Domoticz-Tuya-SmartPlug-Plugin
ln -s /home/pi/.local/lib/python3.5/site-packages/Crypto Crypto
```

2/ Tuya app

The tuya app must be close. This limitation is due to the tuya device itself that support only one connection.

3/ Alternative crypto libraries

PyCryptodome or pyaes can be used instead of pycrypto. 

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
| **DPS** |	1 for single socket device and a list of dps separated by ';' for multisocket device eg. 1;2;3;7
| **DPS group** | None for single socket device and a list of list of dps separated by ':' for multisocket device eg. 1;2 : 3;7
| **DPS always ON** | None for single socket device and a list of dps separated by ; for multisocket device eg. 1;2
| **Debug** | default is 0 |

**DPS** should only includes values that correspond to plug's dps id. Be careful some devices also have timers in the dps state.

**DPS group** can be used to group multiple sockets in one Domoticz switch.

**DPS always ON** can be used to force some sockets to be always on (usb for instance).

Helper scripts get_dps.py turnON.py and turnOFF.py can help:
* to determine the dps list
* to check that the needed information are valid (i.e. devID and Local Key) before using the plugin.

## DevID & Local Key Extraction

Recommanded method:
[`https://github.com/codetheweb/tuyapi/blob/master/docs/SETUP.md`](https://github.com/codetheweb/tuyapi/blob/master/docs/SETUP.md)

All the information can be found here:
[`https://github.com/clach04/python-tuya/`](https://github.com/clach04/python-tuya/)

## Acknowledgements

* Special thanks for all the hard work of [clach04](https://github.com/clach04), [codetheweb](https://github.com/codetheweb/) and all the other contributers on [python-tuya](https://github.com/clach04/python-tuya) and [tuyapi](https://github.com/codetheweb/tuyapi) who have made communicating to Tuya devices possible with open source code.
* Domoticz team
