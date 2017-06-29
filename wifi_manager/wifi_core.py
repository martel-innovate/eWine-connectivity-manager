from wifi import Cell, Scheme
from wifi.exceptions import ConnectionError, InterfaceError

import subprocess
import sched
import time
import sqlite3

MAX_RETRIES = 3
RETRY_AFTER = 5  # seconds
SCHEDULER = sched.scheduler(time.time, time.sleep)


class ApiException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code


class ApiSchemeExistsException(ApiException):
    def __init__(self, message, code, scheme):
        super(ApiSchemeExistsException, self).__init__(message, code)
        self.scheme = scheme


def scheme_all():
    """
    return all schemes stored in /etc/network/interfaces

    :return: list - list of schemes as json string
    """
    schemes = Scheme.all()
    res = []

    for s in schemes:
        res.append(scheme_to_dict(s))

    return res


def cell_all(iface):
    """
    return all cells available on the given network interface, sorted by signal

    :param iface: str - network interface
    :return: list - list of cells as json string
    """

    ssid_enable(iface)

    try:
        cells = Cell.all(iface)
    except InterfaceError as e:
        raise ApiException(e, 404)

    cells.sort(key=lambda cell: cell.signal, reverse=True)

    res = []
    for c in cells:
        res.append(cell_to_dict(c))

    return res


def ssid_save(iface, ssid, passkey, lat, lng, db=None):
    """
    store new network scheme in /etc/network/interfaces
    
    :param iface: str - network interface
    :param ssid: str - network name
    :param passkey: str - authentication passphrase
    :param lat: float - latitude
    :param lng: float - longitude
    :param db: Connection - database handle
    :return: wifi.Scheme - the scheme just created
    """

    ssid_enable(iface)

    try:
        cell = cell_find(iface, ssid)
    except IndexError:
        raise ApiException("cell {}: not found".format(ssid), 404)

    scheme = Scheme.find(iface, ssid)

    # save scheme if it doesn't exist
    if scheme is None:
        # check if passkey is required
        if cell.encrypted and passkey is None:
            raise ApiException("ssid {}: passkey required".format(ssid), 400)

        scheme = Scheme.for_cell(iface, ssid, cell, passkey)
        scheme.save()

        if db is not None:
            # extract hashed passkey from scheme
            if cell.encryption_type.startswith('wpa'):
                passkey = scheme.options['wpa-psk']
            elif cell.encryption_type == 'wep':
                passkey = scheme.options['wireless-key']

            # update database
            try:
                query = "INSERT INTO networks(iface, ssid, passkey, lat, lng) VALUES (?, ?, ?, ?, ?);"
                db.execute(query, (iface, ssid, passkey, lat, lng))
                db.commit()
            except sqlite3.Error as e:
                # failed to sync with database, revert changes
                scheme.delete()
                raise e

        return scheme

    raise ApiSchemeExistsException("ssid {}: scheme already exists".format(ssid), 409, scheme)


def ssid_connect(iface, ssid, passkey, lat, lng, db=None):
    """
    connect to a network

    :param iface: str - network interface
    :param ssid: str - network name
    :param passkey: str - authentication passkey
    :param lat:
    :param lng:
    :param db: Connection - database handle
    :return: int - status code
    """

    def countdown_retry():
        """
        delay new connection attempt
        """

        def countdown_print(s):
            print("retrying connection in {}".format(s))

        def do_nothing():
            pass

        sec = 0
        while sec < RETRY_AFTER:
            SCHEDULER.enter(sec, 1, countdown_print, (RETRY_AFTER - sec,))
            sec += 1

        SCHEDULER.enter(sec, 1, do_nothing, ())
        SCHEDULER.run()

    try:
        scheme = ssid_save(iface, ssid, passkey, lat, lng, db)
    except ApiSchemeExistsException as e:
        scheme = e.scheme
    except ApiException as e:
        raise e

    # try to connect (at least once)
    attempts = 1
    while True:
        try:
            print("connection attempt {}/{}".format(attempts, MAX_RETRIES))
            scheme.activate()
            print("connected to " + ssid)
            break

        except ConnectionError as e:
            print("failed")

            ssid_enable(iface)

            if attempts < MAX_RETRIES:
                # try again
                attempts += 1
                countdown_retry()
            else:
                # failed to connect
                raise ApiException(e, 500)


def ssid_enable(iface):
    """
    enable a network interface

    :param iface: str - network interface
    :return:
    """

    if subprocess.call(["sudo", "ifup", iface]) != 0:
        raise ApiException("error bringing {} up".format(iface), 500)


def ssid_disable(iface):
    """
    disconnect a network interface

    :param iface: str - network interface
    :return:
    """

    if subprocess.call(["sudo", "ifdown", iface]) != 0:
        raise ApiException("error bringing {} down".format(iface), 500)


def ssid_find(iface, ssid):
    """
    find a connection scheme for deletion

    :param iface: str - network interface
    :param ssid: str - network name
    :return: the scheme that matches the arguments
    """

    scheme = Scheme.find(iface, ssid)

    if scheme is None:
        # scheme doesn't exist, raise exception and exit
        raise ApiException("scheme {}: not found".format(ssid), 404)

    return scheme


def ssid_delete(scheme, db=None):
    """
    delete a connection scheme
    
    :param scheme: Scheme - the scheme to be deleted
    :param db: Connection - handle onto sqlite3 database
    :return:
    """

    iface = scheme.interface
    ssid = scheme.name

    scheme.delete()
    print("deleted scheme {}:{}".format(iface, ssid))

    if db is not None:
        # update database
        try:
            db.execute("DELETE FROM networks WHERE iface=? AND ssid=?;", (iface, ssid))
            db.commit()
        except sqlite3.Error as e:
            # failed to sync with database, revert changes
            scheme.save()
            raise e


def ssid_delete_all(db=None):
    """
    delete all connection schemes

    :param db: Connection - handle onto sqlite3 database
    :return: tuple with the total number of schemes and the number of deleted schemes
    """

    schemes = Scheme.all()
    total = 0
    deleted = 0

    for s in schemes:
        total += 1
        try:
            ssid_delete(s, db)
            deleted += 1
        except sqlite3.Error:
            print("scheme not deleted {}:{}".format(s.interface, s.name))

    return total, deleted


def cell_find(iface, ssid):
    """
    look up for cell by network interface and ssid

    :param iface: str - network interface
    :param ssid: str - network name
    :return: wifi.Cell - the first cell that matches the arguments
    """

    cells = Cell.where(iface, lambda c: c.ssid.lower() == ssid.lower())
    # if the cell doesn't exist, cell[0] will raise an IndexError
    cell = cells[0]

    return cell


def cell_to_dict(cell):
    """
    convert a cell object to dictionary

    :param cell: wifi.Cell - the cell object
    :return: dict - the cell as dictionary
    """

    cell_dict = {
        "ssid": cell.ssid,
        "signal": cell.signal,
        "quality": cell.quality,
        "frequency": cell.frequency,
        "bitrates": cell.bitrates,
        "encrypted": cell.encrypted,
        "channel": cell.channel,
        "address": cell.address,
        "mode": cell.mode
    }

    if cell.encrypted:
        cell_dict["encryption_type"] = cell.encryption_type

    return cell_dict


def scheme_to_dict(scheme):
    """
    convert a scheme object to dictionary

    :param scheme: wifi.Scheme - the scheme object
    :return: dict - the scheme as dictionary
    """

    scheme_dict = {
        "interface": scheme.interface,
        "name": scheme.name,
        "options": scheme.options
    }

    return scheme_dict
