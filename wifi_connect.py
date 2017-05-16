#!/usr/bin/python
from __future__ import print_function

import sqlite3
from wifi import Cell, Scheme
from wifi.exceptions import ConnectionError, InterfaceError

import sys, argparse, subprocess, sched, time

MAX_RETRIES = 3
RETRY_AFTER = 3  # seconds
SCHEDULER = sched.scheduler(time.time, time.sleep)


class ApiException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code


class ApiSchemeExistsException(ApiException):
    def __init__(self, message, code, scheme):
        super(ApiSchemeExistsException, self).__init__(message, code)
        self.scheme = scheme


def find_cell(nic, ssid):
    """
    look up for cell by network interface and ssid
    
    :param nic: str - network interface
    :param ssid: str - network name
    :return: wifi.Cell - the first cell that matches the arguments
    """

    cells = Cell.where(nic, lambda c: c.ssid.lower() == ssid.lower())
    # if the cell doesn't exist, cell[0] will raise an IndexError
    cell = cells[0]

    return cell


def ssid_save(nic, ssid, passkey, lat, lng, db=None):
    """
    store new network scheme in /etc/network/interfaces
    
    :param nic: str - network interface
    :param ssid: str - network name
    :param passkey: str - authentication passphrase
    :param lng: 
    :param lat: 
    :param db: Connection - database handle
    :return: wifi.Scheme - the scheme just created
    """

    try:
        cell = find_cell(nic, ssid)
    except IndexError:
        raise ApiException("cell {}: not found".format(ssid), 404)

    scheme = Scheme.find(nic, ssid)

    # save scheme if it doesn't exist
    if scheme is None:
        # check if passkey is required
        if cell.encrypted and passkey is None:
            raise ApiException("ssid {}: passkey required".format(ssid), 400)

        scheme = Scheme.for_cell(nic, ssid, cell, passkey)
        scheme.save()

        if db is not None:
            # extract hashed passkey from scheme
            if cell.encryption_type.startswith('wpa'):
                passkey = scheme.options['wpa-psk']
            elif cell.encryption_type == 'wep':
                passkey = scheme.options['wireless-key']

            # update database
            try:
                query = "INSERT INTO networks(nic, ssid, passkey, lat, lng) VALUES (?, ?, ?, ?, ?);"
                db.execute(query, (nic, ssid, passkey, lat, lng))
                db.commit()
            except sqlite3.Error as e:
                # failed to sync with database, revert changes
                scheme.delete()
                raise e

        return scheme

    raise ApiSchemeExistsException("ssid {}: scheme already exists".format(ssid), 409, scheme)


def ssid_delete(nic, ssid, db=None):
    """
    delete a connection scheme from /etc/network/interfaces
    
    :param nic: str - network interface
    :param ssid: str - network name
    :param db: 
    :return:
    """

    scheme = Scheme.find(nic, ssid)

    if scheme is None:
        # scheme doesn't exist, raise exception and exit
        raise ApiException("scheme {}: not found".format(ssid), 404)

    scheme.delete()
    print("deleted scheme {}".format(ssid))

    # update database
    if db is not None:
        try:
            db.execute("DELETE FROM networks WHERE nic=? AND ssid=?;", (nic, ssid))
            db.commit()
        except sqlite3.Error as e:
            # failed to sync with database, revert changes
            scheme.save()
            raise e


def ssid_connect(nic, ssid, passkey, lat, lng, db=None):
    """
    connect to a network

    :param nic: str - network interface
    :param ssid: str - network name
    :param passkey: str - authentication passkey
    :param lng: 
    :param lat: 
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
        scheme = ssid_save(nic, ssid, passkey, lat, lng, db)
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

            if subprocess.call(["sudo", "ifup", nic]) != 0:
                # make sure interface is up in case of failure
                print("ifup error: nonzero exit code")
                raise ApiException(e.message, 500)

            if attempts < MAX_RETRIES:
                # try again
                attempts += 1
                countdown_retry()
            else:
                # failed to connect
                raise ApiException(e.message, 500)


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


def cell_all(nic):
    """
    return all cells available on the given network interface, sorted by signal
    
    :param nic: str - network interface
    :return: list - list of cells as json string
    """

    res = []

    try:
        cells = Cell.all(nic)
    except InterfaceError as e:
        raise ApiException(e.message, 404)

    cells.sort(key=lambda cell: cell.signal, reverse=True)

    for c in cells:
        res.append(cell_to_dict(c))

    return res


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


def scheme_get(nic, ssid):
    """
    retrieve a scheme by network interface and name
    
    :param nic: str - network interface
    :param ssid: str - network name
    :return: dict - the scheme as dictionary, or None
    """

    schemes = Scheme.all()

    for s in schemes:
        if s.interface == nic and s.name == ssid:
            return scheme_to_dict(s)

    return None


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


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Switch between wireless connections.')
    parser.add_argument('nic', type=str, help='the network interface controller')
    parser.add_argument('ssid', type=str, help='the name of the wireless network')
    parser.add_argument('-p', '--passkey', type=str, help='the passkey for network authentication')
    parser.add_argument('-d', '--delete', help='delete a network configuration scheme', action="store_true")

    args = parser.parse_args()

    if args.delete:
        exit_code = ssid_delete(args.nic, args.ssid)
    else:
        exit_code = ssid_connect(args.nic, args.ssid, args.passkey, None, None)

    sys.exit(exit_code)
