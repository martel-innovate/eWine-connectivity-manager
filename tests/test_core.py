from context import os, core, rest
import unittest
import tempfile


class WifiCoreTestCase(unittest.TestCase):
    """
    Before running the tests, perform the following setup operations:
    - enable 'wlan0'
    - connect to a network
    """

    def setUp(self):
        dir_name = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        rest.app.config['DB_PATH'] = os.path.join(dir_name, 'wifi_manager/schema')
        rest.app.config['DB_SOURCE'] = os.path.join(rest.app.config['DB_PATH'], 'schema.sql')
        self.db_fd, rest.app.config['DB_INSTANCE'] = tempfile.mkstemp()
        rest.app.testing = True

        with rest.app.app_context():
            rest.init_db()
            self.db_ro = rest.get_db()

        self.iface = 'wlan0'

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(rest.app.config['DB_INSTANCE'])

    def test_0a_disable(self):
        code = core.disable(self.iface)
        self.assertEqual(code, 0)

    def test_0b_interfaces(self):
        ifaces = core.interfaces()
        self.assertIsInstance(ifaces, list)
        self.assertNotIn(self.iface, ifaces)

    def test_0c_status(self):
        status = core.status(self.iface)
        self.assertEqual(status, '')

    def test_0d_scan(self):
        self.assertRaises(core.WifiException, core.cell_all, self.iface)

    def test_0e_optimal(self):
        self.assertRaises(core.WifiException, core.optimal, self.iface)

    def test_0f_save(self):
        self.assertRaises(core.WifiException, core.save, self.iface, 'foo', 'foo', self.db_ro)

    def test_0g_connect(self):
        self.assertRaises(core.WifiException, core.connect, self.iface, 'foo', 'foo', self.db_ro)

    def test_1a_enable(self):
        code = core.enable(self.iface)
        self.assertEqual(code, 0)

    def test_1b_interfaces(self):
        ifaces = core.interfaces()
        self.assertIsInstance(ifaces, list)
        self.assertNotIn(self.iface, ifaces)

    def test_1c_status(self):
        status = core.status(self.iface)
        self.assertEqual(status, '')

    def test_1d_scan(self):
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

    def optimal_test(self):
        # the optimal network configuration must be stored before running the test
        optimal = core.optimal(self.iface)
        self.assertIsInstance(optimal, str)
        self.assertTrue(len(optimal) > 0)
        return optimal

    def test_1e_save(self):
        self.assertRaises(core.WifiException, core.save, self.iface, 'foo', 'foo', self.db_ro)

    def test_2a_connect(self):
        optimal = self.optimal_test()
        with rest.app.app_context():
            core.connect(self.iface, optimal, None, rest.get_db())

    def test_2b_interfaces(self):
        ifaces = core.interfaces()
        self.assertIsInstance(ifaces, list)
        self.assertIn(self.iface, ifaces)

    def test_2c_status(self):
        status = core.status(self.iface)
        optimal = self.optimal_test()
        self.assertIsInstance(status, str)
        self.assertEqual(status, optimal)

    def test_3a_delete_all(self):
        with rest.app.app_context():
            total, deleted = core.delete_all(rest.get_db())
        self.assertEquals(total, deleted)

    def test_3b_disable(self):
        code = core.disable(self.iface)
        self.assertEqual(code, 0)

    def test_scheme_all(self):
        schemes = core.scheme_all()
        for obj in schemes:
            iface, name = obj['interface'], obj['name']
            self.assertIsInstance(iface, str)
            self.assertIsInstance(name, str)
            self.assertTrue(len(iface) > 0)
            self.assertTrue(len(name) > 0)

            options = obj['options']
            self.assertIsInstance(options, dict)
            channel, psk, ssid = options['wireless-channel'], options['wpa-psk'], options['wpa-ssid']
            self.assertIsInstance(channel, str)
            self.assertIsInstance(psk, str)
            self.assertIsInstance(ssid, str)
            self.assertTrue(len(channel) > 0)
            self.assertTrue(len(psk) > 0)
            self.assertTrue(len(ssid) > 0)


if __name__ == '__main__':
    unittest.main()
