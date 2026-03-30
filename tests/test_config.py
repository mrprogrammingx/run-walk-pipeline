import os
import unittest

from unittest import mock


class TestConfigGetEnv(unittest.TestCase):
    def test_get_env_returns_value(self):
        import config
        with mock.patch.dict(os.environ, {"TEST_KEY": "value"}, clear=False):
            self.assertEqual(config.get_env("TEST_KEY"), "value")

    def test_get_env_default(self):
        import config
        self.assertEqual(config.get_env("NO_SUCH_KEY", default="d"), "d")


if __name__ == "__main__":
    unittest.main()
