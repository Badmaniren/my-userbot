import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import tempfile
import os

from skills.db_storage import DBStorage

class TestDBStorageInquisitor(unittest.TestCase):
    
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.storage = DBStorage(db_path=self.db_path)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_01_init_creates_database_and_tables(self):
        self.assertTrue(os.path.exists(self.db_path))
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
        self.assertIn("data", tables)
        self.assertIn("cache", tables)

    def test_02_save_and_get_data_success(self):
        key = "target_alpha"
        value = {"status": "compromised", "vectors": [1, 2, 3]}
        self.storage.save_data(key, value)
        retrieved = self.storage.get_data(key)
        self.assertEqual(retrieved, value)

    def test_03_save_data_overwrite_enforced(self):
        key = "volatile_key"
        self.storage.save_data(key, "initial_state")
        self.storage.save_data(key, "overwritten_state")
        self.assertEqual(self.storage.get_data(key), "overwritten_state")

    def test_04_get_data_nonexistent_returns_none(self):
        result = self.storage.get_data("phantom_key_999")
        self.assertIsNone(result)

    def test_05_cache_set_and_get_success(self):
        url = "http://example.com/feed"
        payload = "<rss>data</rss>"
        self.storage.set_cache(url, payload, ttl=300)
        cached_val = self.storage.get_cache(url)
        self.assertEqual(cached_val, payload)

    def test_06_cache_expired_returns_none(self):
        url = "http://example.com/expired"
        payload = "old_data"
        with patch('time.time', return_value=1000.0):
            self.storage.set_cache(url, payload, ttl=50)
        
        with patch('time.time', return_value=1060.0):
            cached_val = self.storage.get_cache(url)
            self.assertIsNone(cached_val)

    def test_07_cache_indefinite_ttl(self):
        url = "http://example.com/immortal"
        payload = "forever"
        self.storage.set_cache(url, payload, ttl=0)
        self.assertEqual(self.storage.get_cache(url), payload)

    def test_08_fail_save_data_invalid_type_raises(self):
        with self.assertRaises((TypeError, sqlite3.InterfaceError)):
            self.storage.save_data("bad_key", lambda x: x)

    def test_09_fail_corrupted_database_connection_raises(self):
        self.storage.conn.close()
        with self.assertRaises(sqlite3.Error):
            self.storage.save_data("test", "data")

    def test_10_fail_get_cache_expired_cleans_up(self):
        url = "http://example.com/cleanup"
        with patch('time.time', return_value=500.0):
            self.storage.set_cache(url, "temp", ttl=10)
        
        with patch('time.time', return_value=600.0):
            self.assertIsNone(self.storage.get_cache(url))
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM cache WHERE key = ?", (url,))
                count = cursor.fetchone()[0]
                self.assertEqual(count, 0)

    def test_11_fail_malformed_json_deserialization(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO data (key, value) VALUES (?, ?)", ("corrupt", "{malformed_json"))
            conn.commit()
        with self.assertRaises(Exception):
            self.storage.get_data("corrupt")

    def test_12_concurrent_access_simulation(self):
        self.storage.save_data("shared", "initial")
        storage2 = DBStorage(db_path=self.db_path)
        storage2.save_data("shared", "mutated_by_second")
        self.assertEqual(self.storage.get_data("shared"), "mutated_by_second")

if __name__ == '__main__':
    unittest.main()