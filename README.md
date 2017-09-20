
## Wifi Connectivity Manager

The app exposes a REST API to control wifi connectivity. Using the right network interface, it is possible to connect and disconnect from wifi networks, but also store and manage network configurations in /etc/network/interfaces and in a Sqlite3 database.

The app runs with [Python 2.7][1].

Make sure [pip][2] is installed on your system, then set up the environment:

    pip install -r requirements.txt

Launch the app by running the bash script: `wifi_manager/interpreter/python_wifi.sh`.

The app listens by default on port 5000. Every request to the REST API must include the following header:

    X-Api-Key: <API KEY HERE>

Here is a list of all API requests, the parameters they accept, and their purpose:

| Request | Parameters | Purpose |
| --- | --- | --- |
| GET /networks |  | retrieve all network configurations stored in /etc/network/interfaces |
| GET /ifaces |  | retrieve all active network interfaces |
| GET /ifaces/`<addresses>` | `addresses`: a non empty string  | retrieve all active network interfaces and their IP addresses |
| GET /scan/`<iface>` | `iface`: the wifi network interface | scan a network interface for available wifi networks |
| GET /status/`<iface>` | `iface`: the wifi network interface | find whether the given interface is connected to a network |
| GET /available/`<iface>` | `iface`: the wifi network interface | find the best Wi-Fi network available, if any |
| GET /location/`<ssid>` | `ssid`: the name of the wifi network | retrieve the location of a Wi-Fi network |
| POST /enable/`<iface>` | `iface`: the wifi network interface | enable a network interface |
| POST /disable/`<iface>` | `iface`: the wifi network interface | disable a network interface |
| POST /networks/`<iface>`:`<ssid>`:`<lat>`:`<lng>` | `iface`: the wifi network interface; `ssid`: the name of the wifi network; `lat`: latitude; `lng`: longitude | store the configuration of an open wifi network in /etc/network/interfaces |
| POST /networks/`<iface>`:`<ssid>`:`<lat>`:`<lng>`:`<passkey>` | `iface`: the wifi network interface; `ssid`: the name of the wifi network; `lat`: latitude; `lng`: longitude; `passkey`: password of the secured wifi network | store the configuration of a secured wifi network in /etc/network/interfaces |
| POST /connect/`<iface>`:`<ssid>`:`<lat>`:`<lng>` | `iface`: the wifi network interface; `ssid`: the name of the wifi network; `lat`: latitude; `lng`: longitude | connect to an open wifi network |
| POST /connect/`<iface>`:`<ssid>`:`<lat>`:`<lng>`:`<passkey>` | `iface`: the wifi network interface; `ssid`: the name of the wifi network; `lat`: latitude; `lng`: longitude; `passkey`: password of the secured wifi network | connect to a secured wifi network |
| DELETE /networks/`<iface>`:`<ssid>` | `iface`: the wifi network interface; `ssid`: the name of the wifi network | delete a network configuration from /etc/network/interfaces and sqlite database |
| DELETE /networks |  | delete all network configurations from /etc/network/interfaces and sqlite database |

[1]:https://www.python.org/download/releases/2.7/
[2]:https://pip.pypa.io/en/stable/installing/




