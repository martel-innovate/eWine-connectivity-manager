from functools import wraps
from flask import Flask, request, g, jsonify
from core import *
import sqlite3

app = Flask(__name__)
app.API_KEY = ''


def require_api_key(route_function):
    """
    authenticate via API key in the request header
    
    :param route_function: the called API endpoint 
    :return: the wrapper authentication function callback
    """

    @wraps(route_function)
    def check_api_key(*args, **kwargs):
        if request.headers.get('X-Api-Key') and request.headers.get('X-Api-Key') == app.API_KEY:
            return route_function(*args, **kwargs)
        else:
            return jsonify(message='unauthorized: wrong or missing api key', code=401)

    return check_api_key


def _get_db():
    """
    get a sqlite3 database handle
    
    :return: sqlite3 database handle
    """

    db = getattr(g, '_database', None)

    if db is None:
        db = g._database = sqlite3.connect(app.config['DB_INSTANCE'])

    return db


def init_db():
    """
    initialize database from sqlite3 script file
    
    :return: 
    """
    with app.app_context():
        db = _get_db()
        with app.open_resource(app.config['DB_SOURCE'], mode='r') as f:
            db.executescript(f.read())
        db.commit()


@app.teardown_appcontext
def _close_connection(exception):
    """
    close connection to sqlite3 database

    :param exception:
    :return: 
    """

    db = getattr(g, '_database', None)

    if db is not None:
        db.close()


@app.errorhandler(WifiException)
def handle_wifi_exception(e):
    resp = jsonify(message=e.message, code=e.code)
    resp.status_code = e.code
    return resp


@app.errorhandler(sqlite3.Error)
def handle_sqlite_exception(e):
    status_code = 500
    resp = jsonify(message=e.message, code=status_code)
    resp.status_code = status_code
    return resp


@app.route('/networks')
@app.route('/networks/<gps>')
@require_api_key
def network_list(gps=''):
    """
    return all schemes stored in /etc/network/interfaces

    :param gps: if non-empty, include GPS location in the response
    :return: JSON response
    """

    gps = bool(gps)

    if gps:
        stored = db_all(_get_db())
    else:
        stored = scheme_all()

    return jsonify(message=stored, code=200)


@app.route('/ifaces')
@app.route('/ifaces/<addresses>')
@require_api_key
def iface_list(addresses=''):
    """
    list network interfaces

    :param addresses: if non-empty, include IP addresses in the response
    :return: JSON response
    """

    ifaces = interfaces(bool(addresses))

    return jsonify(message=ifaces, code=200)


@app.route('/scan/<iface>')
@require_api_key
def network_scan(iface):
    """
    return all wifi networks available on a network interface

    :param iface: network interface
    :return: JSON response
    """

    cells = cell_all(iface)

    return jsonify(message=cells, code=200)


@app.route('/status/<iface>')
@require_api_key
def network_status(iface):
    """
    find out whether the given interface is connected to a network

    :param iface: network interface
    :return: JSON response
    """

    ssid = status(str(iface))

    return jsonify(message=ssid, code=200)


@app.route('/available/<iface>')
@require_api_key
def network_available(iface):
    """
    return the best Wi-Fi network available, if any

    :return: JSON response
    """

    opt = available(iface)

    return jsonify(message=opt, code=200)


@app.route('/location/<ssid>')
@require_api_key
def network_location(ssid):
    """
    fetch last known location of a Wi-Fi network

    :param ssid: network name
    :return: JSON response
    """

    lat, lng = get_last_location(ssid, _get_db())

    return jsonify(message='{},{}'.format(lat, lng), code=200)


@app.route('/enable/<iface>', methods=['POST'])
@require_api_key
def network_enable(iface):
    """
    enable a network interface

    :param iface: network interface
    :return: JSON response
    """

    enable(iface)

    return jsonify(message='enabled {}'.format(iface), code=200)


@app.route('/disable/<iface>', methods=['POST'])
@require_api_key
def network_disable(iface):
    """
    disable a network interface

    :param iface: network interface
    :return: JSON response
    """

    disable(iface)

    return jsonify(message='disabled {}'.format(iface), code=200)


@app.route('/networks/<iface>:<ssid>:<lat>:<lng>', methods=['POST'])
@app.route('/networks/<iface>:<ssid>:<lat>:<lng>:<passkey>', methods=['POST'])
@require_api_key
def network_save(iface, ssid, lat, lng, passkey=None):
    """
    store new network scheme in /etc/network/interfaces

    :param iface: network interface
    :param ssid: network name
    :param lat: latitude
    :param lng: longitude
    :param passkey: authentication passphrase 
    :return: JSON response
    """

    save(iface, ssid, passkey, _get_db(), float(lat), float(lng))

    code = 201
    resp = jsonify(message='created {}:{}'.format(iface, ssid), code=code)
    resp.status_code = code
    return resp


@app.route('/connect/<iface>:<ssid>:<lat>:<lng>', methods=['POST'])
@app.route('/connect/<iface>:<ssid>:<lat>:<lng>:<passkey>', methods=['POST'])
@require_api_key
def network_connect(iface, ssid, lat, lng, passkey=None):
    """
    connect to a network

    :param iface: network interface
    :param ssid: network name
    :param lat: latitude
    :param lng: longitude
    :param passkey: authentication passphrase
    :return: JSON response
    """

    connect(iface, ssid, passkey, _get_db(), float(lat), float(lng))

    return jsonify(message='connected {}:{}'.format(iface, ssid), code=200)


@app.route('/networks/<iface>:<ssid>', methods=['DELETE'])
@app.route('/networks/<iface>:<ssid>:<test>', methods=['DELETE'])
@require_api_key
def network_delete(iface, ssid, test=''):
    """
    delete a connection scheme from /etc/network/interfaces and sqlite database

    :param iface: network interface
    :param ssid: network name
    :param test: if non-empty, perform deletion in the database only (for tests)
    :return: JSON response
    """

    delete(iface, ssid, _get_db(), db_only=bool(test))

    return jsonify(message='deleted {}:{}'.format(iface, ssid), code=200)


@app.route('/networks', methods=['DELETE'])
@app.route('/networks/<test>', methods=['DELETE'])
@require_api_key
def network_delete_all(test=''):
    """
    delete all connection schemes from /etc/network/interfaces and sqlite database

    :param test: if non-empty, perform deletion in the database only (for tests)
    :return: JSON response
    """

    total, deleted = delete_all(_get_db(), db_only=bool(test))

    return jsonify(message='deleted {}/{} schemes'.format(total, deleted), code=200)
