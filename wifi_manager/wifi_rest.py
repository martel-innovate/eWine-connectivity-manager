import os
import sqlite3
from binascii import hexlify
from functools import wraps

from flask import Flask, request, g, jsonify

from wifi_core import ssid_save, ssid_connect, ssid_disconnect, ssid_find, ssid_delete, ssid_delete_all, cell_all, \
    scheme_all, \
    ApiException

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


def get_db():
    """
    get a handle onto sqlite3 database
    
    :return: Connection - handle onto sqlite3 database
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
            db.cursor().executescript(f.read())
        db.commit()


@app.teardown_appcontext
def close_connection(exception):
    """
    close connection to sqlite3 database

    :param exception:
    :return: 
    """

    db = getattr(g, '_database', None)

    if db is not None:
        db.close()


@app.route('/db/networks')
@require_api_key
def db_networks():
    """
    dump table networks

    :return:
    """

    cursor = get_db().execute("SELECT * FROM networks;")
    rows = cursor.fetchall()
    cursor.close()

    return jsonify(message=rows, code=200)


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
    except ApiException as e:
        resp = jsonify(message=e.message, code=e.code)
        resp.status_code = e.code
        return resp

    return jsonify(message=cells, code=200)


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
        ssid_save(iface, ssid, passkey, None, None, get_db())
    except ApiException as e:
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
        ssid_connect(iface, ssid, passkey, None, None, get_db())
    except ApiException as e:
        resp = jsonify(message=e.message, code=e.code)
        resp.status_code = e.code
        return resp

    return jsonify(message='connected {}:{}'.format(iface, ssid), code=200)


@app.route('/disconnect/<iface>', methods=['POST'])
@require_api_key
def network_disconnect(iface):
    """
    disconnect a network interface

    :param iface: str - network interface
    :return:
    """

    try:
        ssid_disconnect(iface)
    except ApiException as e:
        resp = jsonify(message=e.message, code=e.code)
        resp.status_code = e.code
        return resp

    return jsonify(message='disconnected {}'.format(iface), code=200)


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
        ssid_delete(ssid_find(iface, ssid), get_db())
    except ApiException as e:
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

    :return:
    """

    total, deleted = ssid_delete_all(get_db())
    return jsonify(message='deleted {}/{} schemes'.format(total, deleted), code=200)


if __name__ == '__main__':
    API_KEY = hexlify(os.urandom(20)).decode()
    print('api key is: {}'.format(API_KEY))

    app.config['DB_PATH'] = '/home/pi/eWine/wifi_manager/schema'
    app.config['DB_SOURCE'] = os.path.join(app.config['DB_PATH'], 'schema.sql')
    app.config['DB_INSTANCE'] = os.path.join(app.config['DB_PATH'], 'schema.db')

    init_db()
    app.run(host='0.0.0.0')
