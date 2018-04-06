from binascii import hexlify
from flask import json
from context import rest
import os
import unittest
import tempfile
import time

class WifiRestTestCase(unittest.TestCase):
    """
        Before running the tests, make sure at least one network configuration exists and is in range
    """

    def setUp(self):
        dir_name = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        rest.app.config['DB_PATH'] = os.path.join(dir_name, 'wifi_manager/schema')
        rest.app.config['DB_SOURCE'] = os.path.join(rest.app.config['DB_PATH'], 'schema.sql')
        self.db_fd, rest.app.config['DB_INSTANCE'] = tempfile.mkstemp()

        rest.app.testing = True
        self.app = rest.app.test_client()

        with rest.app.app_context():
            rest.init_db()

        rest.app.API_KEY = hexlify(os.urandom(20)).decode()

        self.iface = 'wlan0'
        self.cell = 'foo'
        self.cellnotfound = "cell {}: not found".format(self.cell)
        self.netdown = "Network is down"
        self.netsaved = "created {}:{}"
        self.netconnected = "connected {}:{}"
        self.netalldeleted = "deleted {}/{} schemes"
        self.netnotfound = "scheme {}: not found"
        self.gps_inf = -1000.0

    def tearDown(self):
        time.sleep(20)
        os.close(self.db_fd)
        os.unlink(rest.app.config['DB_INSTANCE'])

    def test_0a_disable(self):
        time.sleep(20)
        resp = self.app.post('/disable/{}'.format(self.iface), headers={'X-Api-Key': rest.app.API_KEY})
        resp_dict = json.loads(resp.get_data())
        self.assertEquals(resp_dict['code'], 200)
        self.assertEquals(resp_dict['message'], 'disabled {}'.format(self.iface))

    def test_0b_scan(self):
        time.sleep(20)
        resp = self.app.get('/scan/{}'.format(self.iface), headers={'X-Api-Key': rest.app.API_KEY})
        resp_dict = json.loads(resp.get_data())
        self.assertEquals(resp_dict['code'], 404)
        msg = resp_dict['message']
        self.assertTrue(self.iface in msg)
        self.assertTrue(self.netdown in msg)

    def test_0c_available(self):
        time.sleep(20)
        resp = self.app.get('/available/{}'.format(self.iface), headers={'X-Api-Key': rest.app.API_KEY})
        resp_dict = json.loads(resp.get_data())
        self.assertEquals(resp_dict['code'], 404)
        msg = resp_dict['message']
        self.assertTrue(self.iface in msg)
        self.assertTrue(self.netdown in msg)

    def test_0d_save(self):
        time.sleep(20)
        resp = self.app.post('/networks/{}:foo:{}:{}'.format(self.iface, self.gps_inf, self.gps_inf),
                             headers={'X-Api-Key': rest.app.API_KEY})
        resp_dict = json.loads(resp.get_data())
        self.assertEquals(resp_dict['code'], 404)
        msg = resp_dict['message']
        self.assertTrue(self.iface in msg)
        self.assertTrue(self.netdown in msg)

    def test_0e_connect(self):
        time.sleep(20)
        resp = self.app.post('/connect/{}:foo:{}:{}'.format(self.iface, self.gps_inf, self.gps_inf),
                             headers={'X-Api-Key': rest.app.API_KEY})
        resp_dict = json.loads(resp.get_data())
        self.assertEquals(resp_dict['code'], 404)
        msg = resp_dict['message']
        self.assertTrue(self.iface in msg)
        self.assertTrue(self.netdown in msg)

    def test_1a_enable(self):
        time.sleep(20)
        resp = self.app.post('/enable/{}'.format(self.iface), headers={'X-Api-Key': rest.app.API_KEY})
        resp_dict = json.loads(resp.get_data())
        self.assertEquals(resp_dict['code'], 200)
        self.assertEquals(resp_dict['message'], 'enabled {}'.format(self.iface))

    def test_1b_scan(self):
        time.sleep(20)
        resp = self.app.get('/scan/{}'.format(self.iface), headers={'X-Api-Key': rest.app.API_KEY})
        resp_dict = json.loads(resp.get_data())
        self.assertEquals(resp_dict['code'], 200)
        self.assertIsInstance(resp_dict['message'], list)

    def available_test(self):
        time.sleep(20)
        resp = self.app.get('/available/{}'.format(self.iface), headers={'X-Api-Key': rest.app.API_KEY})
        resp_dict = json.loads(resp.get_data())
        self.assertEquals(resp_dict['code'], 200)
        self.assertIsInstance(resp_dict['message'], unicode)
        self.assertTrue(len(resp_dict['message']) > 0)
        return resp_dict['message']

    def test_1d_save(self):
        time.sleep(20)
        avail = self.available_test()
        resp = self.app.post('/networks/{}:{}:{}:{}'.format(self.iface, avail, self.gps_inf, self.gps_inf),
                             headers={'X-Api-Key': rest.app.API_KEY})
        resp_dict = json.loads(resp.get_data())
        self.assertEquals(resp_dict['code'], 201)
        self.assertEquals(resp_dict['message'], self.netsaved.format(self.iface, avail))

    def test_1e_connect(self):
        time.sleep(20)
        avail = self.available_test()
        resp = self.app.post('/connect/{}:{}:{}:{}'.format(self.iface, avail, self.gps_inf, self.gps_inf),
                             headers={'X-Api-Key': rest.app.API_KEY})
        resp_dict = json.loads(resp.get_data())
        self.assertEquals(resp_dict['code'], 200)
        self.assertEquals(resp_dict['message'], self.netconnected.format(self.iface, avail))

    def test_1f_location(self):
        time.sleep(20)
        avail = self.available_test()
        resp = self.app.get('/location/{}'.format(avail), headers={'X-Api-Key': rest.app.API_KEY})
        resp_dict = json.loads(resp.get_data())
        msg = resp_dict['message']
        self.assertEquals(resp_dict['code'], 200)
        self.assertIsInstance(msg, unicode)
        values = msg.split(",")
        self.assertEquals(len(values), 2)
        lat = float(values[0])
        lng = float(values[1])
        self.assertTrue(lat, self.gps_inf)
        self.assertTrue(lng, self.gps_inf)

    def stored_networks(self):
        time.sleep(20)
        resp = self.app.get('/networks', headers={'X-Api-Key': rest.app.API_KEY})
        resp_dict = json.loads(resp.get_data())
        self.assertEquals(resp_dict['code'], 200)
        self.assertIsInstance(resp_dict['message'], list)
        return len(resp_dict['message'])

    def test_2a_delete_all(self):
        time.sleep(20)
        n = self.stored_networks()
        resp = self.app.delete('/networks/test', headers={'X-Api-Key': rest.app.API_KEY})
        resp_dict = json.loads(resp.get_data())
        self.assertEquals(resp_dict['code'], 200)
        self.assertEquals(resp_dict['message'], self.netalldeleted.format(n, n))

    def test_2b_delete(self):
        time.sleep(20)
        resp = self.app.delete('/networks/{}:foo'.format(self.iface), headers={'X-Api-Key': rest.app.API_KEY})
        resp_dict = json.loads(resp.get_data())
        self.assertEquals(resp_dict['code'], 404)
        self.assertEquals(resp_dict['message'], self.netnotfound.format('foo'))

    def test_2c_location(self):
        time.sleep(20)
        avail = self.available_test()
        resp = self.app.get('/location/{}'.format(avail), headers={'X-Api-Key': rest.app.API_KEY})
        resp_dict = json.loads(resp.get_data())
        msg = resp_dict['message']
        self.assertEquals(resp_dict['code'], 200)
        self.assertIsInstance(msg, unicode)
        values = msg.split(",")
        self.assertEquals(len(values), 2)
        lat = float(values[0])
        lng = float(values[1])
        self.assertEquals(lat, self.gps_inf)
        self.assertEquals(lng, self.gps_inf)

    def test_2d_disable(self):
        time.sleep(20)
        resp = self.app.post('/disable/{}'.format(self.iface), headers={'X-Api-Key': rest.app.API_KEY})
        resp_dict = json.loads(resp.get_data())
        self.assertEquals(resp_dict['code'], 200)
        self.assertEquals(resp_dict['message'], 'disabled {}'.format(self.iface))

    def single_test_api_key(self, route, method):
        time.sleep(20)
        if method == 'GET':
            resp = self.app.get(route)
        elif method == 'POST':
            resp = self.app.post(route)
        elif method == 'DELETE':
            resp = self.app.delete(route)

        resp_dict = json.loads(resp.get_data())

        self.assertEqual(resp_dict['message'], 'unauthorized: wrong or missing api key')
        self.assertEqual(resp_dict['code'], 401)

    def test_all_api_key(self):
        time.sleep(20)
        self.single_test_api_key('/networks', 'GET')
        self.single_test_api_key('/ifaces', 'GET')
        self.single_test_api_key('/scan/{}'.format(self.iface), 'GET')
        self.single_test_api_key('/status/{}'.format(self.iface), 'GET')
        self.single_test_api_key('/available/{}'.format(self.iface), 'GET')
        self.single_test_api_key('/location/ssid', 'GET')
        self.single_test_api_key('/enable/{}'.format(self.iface), 'POST')
        self.single_test_api_key('/disable/{}'.format(self.iface), 'POST')
        self.single_test_api_key('/networks/iface:ssid:{}:{}'.format(self.gps_inf, self.gps_inf), 'POST')
        self.single_test_api_key('/connect/iface:ssid:{}:{}'.format(self.gps_inf, self.gps_inf), 'POST')
        self.single_test_api_key('/networks/iface:ssid', 'DELETE')
        self.single_test_api_key('/networks', 'DELETE')

    def test_networks(self):
        time.sleep(20)
        resp = self.app.get('/networks', headers={'X-Api-Key': rest.app.API_KEY})
        resp_dict = json.loads(resp.get_data())
        self.assertEquals(resp_dict['code'], 200)
        self.assertIsInstance(resp_dict['message'], list)

    def test_ifaces(self):
        time.sleep(20)
        resp1 = self.app.get('/ifaces', headers={'X-Api-Key': rest.app.API_KEY})
        resp1_dict = json.loads(resp1.get_data())
        self.assertEquals(resp1_dict['code'], 200)
        self.assertIsInstance(resp1_dict['message'], list)

        resp2 = self.app.get('/ifaces/addr', headers={'X-Api-Key': rest.app.API_KEY})
        resp2_dict = json.loads(resp2.get_data())
        self.assertEquals(resp2_dict['code'], 200)
        self.assertIsInstance(resp2_dict['message'], list)

    def test_status(self):
        time.sleep(20)
        resp = self.app.get('/status/{}'.format(self.iface), headers={'X-Api-Key': rest.app.API_KEY})
        resp_dict = json.loads(resp.get_data())
        self.assertEquals(resp_dict['code'], 200)
        self.assertIsInstance(resp_dict['message'], unicode)


if __name__ == '__main__':
    unittest.main()
