from context import os, core, rest

import unittest
import tempfile


class WifiCoreTestCase(unittest.TestCase):

    def setUp(self):
        self.iface = 'wlan0'

        rest.app.config['DB_PATH'] = '/home/pi/eWine-connectivity-manager/wifi_manager/schema'
        rest.app.config['DB_SOURCE'] = os.path.join(rest.app.config['DB_PATH'], 'schema.sql')
        self.db_fd, rest.app.config['DB_INSTANCE'] = tempfile.mkstemp()

        rest.app.testing = True
        self.app = rest.app.test_client()

        with rest.app.app_context():
            rest.init_db()

    def test_1_enable(self):
        code = core.enable(self.iface)
        self.assertEqual(code, 0)

        ifaces = core.interfaces()
        self.assertNotIn(self.iface, ifaces)

    def test_2_connect(self):
        optimal = core.optimal(self.iface)
        self.assertTrue(len(optimal) > 0)

        core.connect(self.iface, optimal, None, self.db_fd)

        ifaces = core.interfaces()
        self.assertIn(self.iface, ifaces)

    def test_3_disable(self):
        code = core.disable(self.iface)
        self.assertEqual(code, 0)

        ifaces = core.interfaces()
        self.assertNotIn(self.iface, ifaces)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(rest.app.config['DB_INSTANCE'])


if __name__ == '__main__':
    unittest.main()

