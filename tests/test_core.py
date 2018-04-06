from context import os, core
import time
import pdb
import unittest
import sqlite3
import tempfile


class WifiCoreTestCase(unittest.TestCase):
    """
        Before running the tests, make sure at least one network configuration exists and is in range
    """

    def setUp(self):
        dir_name = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_source = os.path.join(dir_name, 'wifi_manager/schema/schema.sql')

        self.db_fd, self.db_name = tempfile.mkstemp()
        self.db = sqlite3.connect(self.db_name)

        with open(db_source) as f:
            self.db.executescript(f.read())
        self.db.commit()

        self.iface = 'wlan0'
        self.gps_inf = -1000.0

    def tearDown(self):
        time.sleep(20)
        os.close(self.db_fd)
        os.unlink(self.db_name)

    def test_0a_disable(self):
        time.sleep(20)
        code = core.disable(self.iface)
        self.assertEqual(code, 0)

    def test_0b_interfaces(self):
        time.sleep(20)
        ifaces = core.interfaces()
        self.assertIsInstance(ifaces, list)
        self.assertNotIn(self.iface, ifaces)

    def test_0c_status(self):
        time.sleep(20)
        status = core.status(self.iface)
        self.assertEqual(status, '')

    def test_0d_scan(self):
        time.sleep(20)
        self.assertRaises(core.WifiException, core.cell_all, self.iface)

    def test_0e_available(self):
        time.sleep(20)
        self.assertRaises(core.WifiException, core.available, self.iface)

    def test_0f_save(self):
        time.sleep(20)
        self.assertRaises(core.WifiException, core.save, self.iface, 'foo', 'foo', self.db)

    def test_0g_connect(self):
        time.sleep(20)
        self.assertRaises(core.WifiException, core.connect, self.iface, 'foo', 'foo', self.db)

    def test_1a_enable(self):
        time.sleep(20)
        code = core.enable(self.iface)
        self.assertEqual(code, 0)

    def test_1b_interfaces(self):
        time.sleep(20)
        ifaces = core.interfaces()
        self.assertIsInstance(ifaces, list)
        self.assertIn(self.iface, ifaces)

    def test_1c_status(self):
        time.sleep(20)
        status = core.status(self.iface)
        self.assertNotEqual(status, '')
        
    def test_1d_scan(self):
        time.sleep(20)
        cells = core.cell_all(self.iface)
        self.assertIsInstance(cells, list)

        for c in cells:
            self.assertIsInstance(c["ssid"], unicode)
            self.assertIsInstance(c["signal"], int)
            self.assertIsInstance(c["quality"], unicode)
            self.assertIsInstance(c["frequency"], unicode)
            self.assertIsInstance(c["bitrates"], list)
            self.assertIsInstance(c["encrypted"], bool)
            self.assertIsInstance(c["channel"], int)
            self.assertIsInstance(c["address"], unicode)
            self.assertIsInstance(c["mode"], unicode)

            if c["encrypted"]:
                self.assertIsInstance(c["encryption_type"], str)

    def available_test(self):
        time.sleep(20)
        # the network configuration must be stored before running the test
        avail = core.available(self.iface)
        self.assertIsInstance(avail, str)
        self.assertTrue(len(avail) > 0)
        return avail

    def test_1e_save(self):
        time.sleep(20)
        self.assertRaises(core.WifiException, core.save, self.iface, 'foo', 'foo', self.db)

    def test_2a_connect(self):
        time.sleep(20)
        avail = self.available_test()
        core.connect(self.iface, avail, None, self.db)

    def test_2b_interfaces(self):
        time.sleep(20)
        ifaces = core.interfaces()
        self.assertIsInstance(ifaces, list)
        self.assertIn(self.iface, ifaces)

    def test_2c_status(self):
        time.sleep(20)
        status = core.status(self.iface)
        avail = self.available_test()
        self.assertIsInstance(status, str)
        self.assertEqual(status, avail)

    def test_2d_location(self):
        time.sleep(20)
        avail = self.available_test()
        lat, lng = core.get_last_location(avail, self.db)
        self.assertIsInstance(lat, float)
        self.assertIsInstance(lng, float)
        self.assertEquals(lat, self.gps_inf)
        self.assertEquals(lng, self.gps_inf)

    def test_3a_delete_all(self):
        time.sleep(20)
        total, deleted = core.delete_all(self.db, db_only=True)
        self.assertEquals(total, deleted)

    def test_3b_location(self):
        time.sleep(20)
        avail = self.available_test()
        lat, lng = core.get_last_location(avail, self.db)
        self.assertIsInstance(lat, float)
        self.assertIsInstance(lng, float)
        self.assertEquals(lat, self.gps_inf)
        self.assertEquals(lng, self.gps_inf)

    def test_3c_disable(self):
        time.sleep(20)
        code = core.disable(self.iface)
        self.assertEqual(code, 0)

    def test_scheme_all(self):
        time.sleep(20)
        schemes = core.scheme_all()
        for obj in schemes:
            iface, name = obj['interface'], obj['name']
            self.assertIsInstance(iface, str)
            self.assertIsInstance(name, str)
            self.assertTrue(len(iface) > 0)
            self.assertTrue(len(name) > 0)

            options = obj['options']
            self.assertIsInstance(options, dict)
            channel, psk, ssid = options.get('wireless-channel'), options.get('wpa-psk'), options.get('wpa-ssid')
            if channel is not None:
                self.assertIsInstance(channel, str)
                print("channel is defined")
            else:
                print("channel is not defined")
                
            if psk is not None:
                self.assertIsInstance(psk, str)
                print("psk is defined")
            else:
                print("psk is not defined")
                
            if ssid is not None:    
                self.assertIsInstance(ssid, str)
                print("ssid is defined")
            else:
                print("ssid is not defined")
                
            if channel is not None:
                self.assertTrue(len(channel) > 0)
                print("channel is true")
            else:
                print("channel is false")
                
            if psk is not None:
                self.assertTrue(len(psk) > 0)
                print("psk is true")
            else:
                print("psk is false")
                
            if ssid is not None:
                self.assertTrue(len(ssid) > 0)
                print("ssid is true")
            else:
                print("ssid is false")


if __name__ == '__main__':
    unittest.main()
