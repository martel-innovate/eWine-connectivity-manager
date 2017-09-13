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


def get_db():
    """
    get a handle onto sqlite3 database
    
    :return: handle onto sqlite3 database
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
        db = get_db()
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
@require_api_key
def network_list():
    """
    return all schemes stored in /etc/network/interfaces
    
    :return: response as JSON
    """

    stored = scheme_all()

    return jsonify(message=stored, code=200)


@app.route('/ifaces')
@app.route('/ifaces/<addresses>')
@require_api_key
def iface_list(addresses=''):
    """
    list network interfaces

    :return: response as JSON
    """

    ifaces = interfaces(bool(addresses))

    return jsonify(message=ifaces, code=200)


@app.route('/scan/<iface>')
@require_api_key
def network_scan(iface):
    """
    return all wifi networks available on a network interface

    :param iface: network interface
    :return: response as JSON
    """

    cells = cell_all(iface)

    return jsonify(message=cells, code=200)


@app.route('/status/<iface>')
@require_api_key
def network_status(iface):
    """
    find whether the given interface is connected to a network

    :param iface: network interface
    :return: response as JSON
    """

    ssid = status(str(iface))

    return jsonify(message=ssid, code=200)


@app.route('/enable/<iface>', methods=['POST'])
@require_api_key
def network_enable(iface):
    """
    enable a network interface

    :param iface: network interface
    :return: response as JSON
    """

    enable(iface)

    return jsonify(message='enabled {}'.format(iface), code=200)


@app.route('/disable/<iface>', methods=['POST'])
@require_api_key
def network_disable(iface):
    """
    disable a network interface

    :param iface: network interface
    :return: response as JSON
    """

    disable(iface)

    return jsonify(message='disabled {}'.format(iface), code=200)


@app.route('/networks/<iface>:<ssid>', methods=['POST'])
@app.route('/networks/<iface>:<ssid>:<passkey>', methods=['POST'])
@require_api_key
def network_save(iface, ssid, passkey=None):
    """
    store new network scheme in /etc/network/interfaces
    
    :param iface: network interface
    :param ssid: network name
    :param passkey: authentication passphrase 
    :return: response as JSON
    """

    save(iface, ssid, passkey, db=get_db())

    code = 201
    resp = jsonify(message='created {}:{}'.format(iface, ssid), code=code)
    resp.status_code = code
    return resp


@app.route('/optimal/<iface>')
@require_api_key
def network_optimal(iface):
    """
    return the optimal Wi-Fi network, if any

    :return: response as JSON
    """

    opt = optimal(iface)

    return jsonify(message=opt, code=200)


@app.route('/connect/<iface>:<ssid>', methods=['POST'])
@app.route('/connect/<iface>:<ssid>:<passkey>', methods=['POST'])
@require_api_key
def network_connect(iface, ssid, passkey=None):
    """
    connect to a network

    :param iface: network interface
    :param ssid: network name
    :param passkey: authentication passphrase
    :return: response as JSON
    """

    connect(iface, ssid, passkey, db=get_db())

    return jsonify(message='connected {}:{}'.format(iface, ssid), code=200)


@app.route('/networks/<iface>:<ssid>', methods=['DELETE'])
@app.route('/networks/<iface>:<ssid>:<test>', methods=['DELETE'])
@require_api_key
def network_delete(iface, ssid, test=''):
    """
    delete a connection scheme from /etc/network/interfaces and sqlite database

    :param iface: network interface
    :param ssid: network name
    :param test: for tests only
    :return: response as JSON
    """

    delete(iface, ssid, get_db(), db_only=bool(test))

    return jsonify(message='deleted {}:{}'.format(iface, ssid), code=200)


@app.route('/networks', methods=['DELETE'])
@app.route('/networks/<test>', methods=['DELETE'])
@require_api_key
def network_delete_all(test=''):
    """
    delete all connection schemes from /etc/network/interfaces and sqlite database

    :param test: for tests only
    :return: response as JSON
    """

    total, deleted = delete_all(get_db(), db_only=bool(test))

    return jsonify(message='deleted {}/{} schemes'.format(total, deleted), code=200)
