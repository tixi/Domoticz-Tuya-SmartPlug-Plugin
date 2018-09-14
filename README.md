# Domoticz-Tuya-SmartPlug-Plugin

A Domoticz plugin to manage Tuya Smart Plug

## ONLY TESTED FOR Raspberry Pi

With Python version 3.5 & Domoticz version 4.9700 (stable) and 4.9999 (beta)

## Prerequisites

This plugin is based on the latest pytuya Python library. For the installation of this library,
follow the Installation guide below since pip will not install the latest version commited few days ago.
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

## Known issue

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
| **Replay** | default is Yes |
| **Debug** | default is False |

Replay indicates that a command (on/off) will be replay in case of failure except when the Smart Plug is not connected.

## DevID & Local Key Extraction

All the information can be found here:
[`https://github.com/clach04/python-tuya/`](https://github.com/clach04/python-tuya/)

## Acknowledgements

  * Special thanks for all the hard work of [codetheweb](https://github.com/codetheweb/), [clach04](https://github.com/clach04), [blackrozes](https://github.com/blackrozes), [jepsonrob](https://github.com/jepsonrob), and all the other contributers on [tuyapi](https://github.com/codetheweb/tuyapi) and [python-tuya](https://github.com/clach04/python-tuya) who have made communicating to Tuya devices possible with open source code.
* Domoticz team
