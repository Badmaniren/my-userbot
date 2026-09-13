import unittest
import os
import json
import time
import shutil
from unittest.mock import patch
from skills.file_cache import FileCache

class TestFileCacheInquisitor(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = 'test_cache_sandbox'
        self.cache = FileCache(cache_dir=self.test_dir, default_ttl=1)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_basic_set_and_get(self):
        self.cache.set('key1', {'data': 123})
        self.assertEqual(self.cache.get('key1'), {'data': 123})

    def test_ttl_expiration(self):
        self.cache.set('key_ttl', 'expired_data', ttl=1)
        self.assertEqual(self.cache.get('key_ttl'), 'expired_data')
        time.sleep(1.1)
        self.assertIsNone(self.cache.get('key_ttl'))

    def test_invalid_types_and_empty_keys(self):
        with self.assertRaises((TypeError, ValueError, KeyError)):
            self.cache.set('', 'value')
        with self.assertRaises((TypeError, ValueError, KeyError)):
            self.cache.get(None)
        
        self.cache.set('valid_key', None)
        self.assertIsNone(self.cache.get('valid_key'))

    def test_corrupted_json_file(self):
        self.cache.set('broken', 'data')
        file_path = os.path.join(self.test_dir, 'broken.json')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("{ CORRUPTED JSON CONTENT")
            
        self.assertIsNone(self.cache.get('broken'))

    @patch('time.time')
    def test_time_mocking(self, mock_time):
        mock_time.return_value = 1000.0
        self.cache.set('mock_key', 'value', ttl=50)
        
        mock_time.return_value = 1040.0
        self.assertEqual(self.cache.get('mock_key'), 'value')
        
        mock_time.return_value = 1051.0
        self.assertIsNone(self.cache.get('mock_key'))

if __name__ == '__main__':
    unittest.main()