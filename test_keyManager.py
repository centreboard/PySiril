from unittest import TestCase
from SirilParser import key_manager


class TestKeyManager(TestCase):
    def test_get_key_original(self):
        to_replace = ["test", "(+23.4.4)", "repeat{/1234/: break}"]
        for replace in to_replace:
            key = key_manager.get_key(replace)
            self.assertIn(key, key_manager.original)
            self.assertNotIn("`@", key_manager.original)
            self.assertEqual(replace, key_manager.get_original(key))
            line = "test123, {}, +-1".format(key)
            self.assertEqual(line.replace(key, replace), key_manager.get_original(line))
