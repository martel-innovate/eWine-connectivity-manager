import os
from binascii import hexlify
from functools import wraps

from flask import Flask, request, g, jsonify

from wifi_core import *

app = Flask(__name__)


def require_api_key(route_function):
    """
    authenticate via API key in the request header
    
    :param route_function: the called API endpoint 
    :return: the wrapper authentication function callback
    """

    @wraps(route_function)
    def check_api_key(*args, **kwargs):
        if request.headers.get('X-api-key') and request.headers.get('X-api-key') == API_KEY:
            return route_function(*args, **kwargs)
        else:
            return jsonify(message='unauthorized: wrong or missing api key', code=401)

    return check_api_key


def _get_db():
    """
    get a handle onto sqlite3 database
    
    :return: handle onto sqlite3 database
    """

    db = getattr(g, '_database', None)

    if db is None:
        db = g._database = sqlite3.connect(app.config['DB_INSTANCE'])

    return db


def _init_db():
    """
    initialize database from sqlite3 script file
    
    :return: 
    """
    with app.app_context():
        db = _get_db()
        with app.open_resource(app.config['DB_SOURCE'], mode='r') as f:
            db.cursor().executescript(f.read())
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


@app.route('/networks')
@require_api_key
def network_list():
    """
    return all schemes stored in /etc/network/interfaces
    
    :return: response as JSON 
    """

    schemes = scheme_all()
    return jsonify(message=schemes, code=200)


@app.route('/networks/<iface>')
@require_api_key
def network_scan(iface):
    """
    return all wifi networks available on a network interface

    :param iface: network interface
    :return: response as JSON
    """

    try:
        cells = cell_all(iface)
    except WifiException as e:
        resp = jsonify(message=e.message, code=e.code)
        resp.status_code = e.code
        return resp

    return jsonify(message=cells, code=200)


@app.route('/status/<iface>')
@require_api_key
def network_status(iface):
    """
    find whether the given interface is connected to a network

    :param iface: network interface
    :return: response as JSON
    """

    ssid = wifi_status(iface)
    return jsonify(message=ssid, code=200)


@app.route('/enable/<iface>', methods=['POST'])
@require_api_key
def network_enable(iface):
    """
    enable a network interface

    :param iface: network interface
    :return:
    """

    try:
        wifi_enable(iface)
    except WifiException as e:
        resp = jsonify(message=e.message, code=e.code)
        resp.status_code = e.code
        return resp

    return jsonify(message='enabled {}'.format(iface), code=200)


@app.route('/disable/<iface>', methods=['POST'])
@require_api_key
def network_disable(iface):
    """
    disable a network interface

    :param iface: network interface
    :return:
    """

    try:
        wifi_disable(iface)
    except WifiException as e:
        resp = jsonify(message=e.message, code=e.code)
        resp.status_code = e.code
        return resp

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

    try:
        ssid_save(iface, ssid, passkey, db=_get_db())
    except WifiException as e:
        resp = jsonify(message=e.message, code=e.code)
        resp.status_code = e.code
        return resp
    except sqlite3.Error as e:
        code = 500
        resp = jsonify(message=e, code=code)
        resp.status_code = code
        return resp

    code = 201
    resp = jsonify(message='created {}:{}'.format(iface, ssid), code=code)
    resp.status_code = code
    return resp


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

    try:
        ssid_connect(iface, ssid, passkey, db=_get_db())
    except WifiException as e:
        resp = jsonify(message=e.message, code=e.code)
        resp.status_code = e.code
        return resp

    return jsonify(message='connected {}:{}'.format(iface, ssid), code=200)


@app.route('/networks/<iface>:<ssid>', methods=['DELETE'])
@require_api_key
def network_delete(iface, ssid):
    """
    delete a connection scheme from /etc/network/interfaces and sqlite database

    :param iface: network interface
    :param ssid: network name 
    :return: response as JSON
    """

    try:
        ssid_delete(iface, ssid, _get_db())
    except WifiException as e:
        resp = jsonify(message=e.message, code=e.code)
        resp.status_code = e.code
        return resp
    except sqlite3.Error as e:
        code = 500
        resp = jsonify(message=e, code=code)
        resp.status_code = code
        return resp

    return jsonify(message='deleted {}:{}'.format(iface, ssid), code=200)


@app.route('/networks', methods=['DELETE'])
@require_api_key
def network_delete_all():
    """
    delete all connection schemes from /etc/network/interfaces and sqlite database

    :return: response as JSON
    """

    total, deleted = ssid_delete_all(_get_db())
    return jsonify(message='deleted {}/{} schemes'.format(total, deleted), code=200)


if __name__ == '__main__':
    API_KEY = hexlify(os.urandom(20)).decode()
    print('api key is: {}'.format(API_KEY))

    app.config['DB_PATH'] = '/home/pi/eWine-connectivity-manager/wifi_manager/schema'
    app.config['DB_SOURCE'] = os.path.join(app.config['DB_PATH'], 'schema.sql')
    app.config['DB_INSTANCE'] = os.path.join(app.config['DB_PATH'], 'schema.db')

    _init_db()
    app.run(host='0.0.0.0')
