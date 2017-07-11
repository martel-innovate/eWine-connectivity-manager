from wifi_manager import wifi_rest

import os
import unittest
import tempfile


class WifiTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, wifi_rest.app.config['DATABASE'] = tempfile.mkstemp()
        wifi_rest.app.testing = True
        self.app = wifi_rest.app.test_client()
        with wifi_rest.app.app_context():
            wifi_rest._init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(wifi_rest.app.config['DATABASE'])


if __name__ == '__main__':
    unittest.main()
