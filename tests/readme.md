# Run test eWine-Connectivity-Manager

## RUNNING
* open 2 shell tabs
In the 1st shell : 
	$ /home/pi/eWine-connectivity-manager/wifi_manager/interpreter/python_venv.sh

* In the 2nd shell:
	$ cd /home/pi/eWine-connectivity-manager/
	$ . .venv/bin/activate

	$ sudo ifup wlan0 		#to activate the wireless card, if it is down
	$ wifi list			#once time command to check if your wifi connection is stored
	$ wifi add yournamewifi SSID	#USE this command ONLY if your wifi connection is not in the list --- more information ../wifi/docs/wifi_command.rst
	$ cd tests
	$ sudo python test_core.py		#launch test

	if the test fails, try to launch these commands:
		sudo ifup wlan0
		sudo wifi connect SSID		#even if your wireless card is already connected
		sudo python test_core.py		#launch test