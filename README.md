
## Wifi Connectivity Manager

The app exposes a REST API to control wifi connectivity. Using the right network interface, it is possible to connect and disconnect from wifi networks, but also store and manage network configurations in /etc/network/interfaces and in a Sqlite3 database.

Launch the app by running the bash script: `wifi_manager/interpreter/python_wifi.sh`.

The app listens by default on port 5000. Every request to the REST API must include the following header:

    X-api-key: <API KEY HERE>

Here is a list of all API requests, the parameters they accept, and their purpose:

| Request | Parameters | Purpose |
| --- | --- | --- |
| GET /networks |  | retrieve all network configurations stored in /etc/network/interfaces |
| GET /ifaces |  | retrieve all active network interfaces |
| GET /ifaces/<addresses> |  | retrieve all active network interfaces |
| GET /scan/`<iface>` | `iface`: the wifi network interface | scan a network interface for available wifi networks |
| GET /status/`<iface>` | `iface`: same as above | find whether the given interface is connected to a network |
| POST /enable/`<iface>` | `iface`: same as above | enable a network interface |
| POST /disable/`<iface>` | `iface`: same as above | disable a network interface |
| POST /networks/`<iface>`:`<ssid>` | `iface`: same as above; `ssid`: the name of the wifi network | store the configuration of an open wifi network in /etc/network/interfaces |
| POST /networks/`<iface>`:`<ssid>`:`<passkey>` | `iface`: same as above; `ssid`: same as above; `passkey`: password of the secured wifi network | store the configuration of a secured wifi network in /etc/network/interfaces |
| GET /optimal/`<iface>` | `iface`: same as above | find an optimal Wi-Fi network, if any |
| POST /connect/`<iface>`:`<ssid>` | `iface`: same as above; `ssid`: same as above | connect to an open wifi network |
| POST /connect/`<iface>`:`<ssid>`:`<passkey>` | `iface`: same as above; `ssid`: same as above; `passkey`: same as above | connect to a secured wifi network |
| DELETE /networks/`<iface>`:`<ssid>` | `iface`: same as above; `ssid`: same as above | delete a network configuration from /etc/network/interfaces and sqlite database |
| DELETE /networks |  | delete all network configurations from /etc/network/interfaces and sqlite database |




