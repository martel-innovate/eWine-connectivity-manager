from context import rest

import os
import unittest
import tempfile


class WifiRestTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, rest.app.config['DB_INSTANCE'] = tempfile.mkstemp()
        rest.app.testing = True
        self.app = rest.app.test_client()
        with rest.app.app_context():
            rest.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(rest.app.config['DB_INSTANCE'])


if __name__ == '__main__':
    unittest.main()
