import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile

from skills.compressed_db_storage import CompressedDBStorage
from skills.db_storage import DBStorage
from skills.payload_compressor import PayloadCompressor


class TestCompressedDBStorage(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.test_dir.name, "test_storage.db")
        self.storage = CompressedDBStorage(self.db_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_initialization(self):
        self.assertIsInstance(self.storage.db, DBStorage)
        self.assertIsInstance(self.storage.compressor, PayloadCompressor)

    def test_save_and_get_compressed_data(self):
        test_key = "artifact_1"
        test_payload = {"status": "success", "data": [1, 2, 3, 4, 5]}

        self.storage.save_compressed_data(test_key, test_payload)
        retrieved_data = self.storage.get_compressed_data(test_key)

        self.assertEqual(retrieved_data, test_payload)

    def test_get_nonexistent_data(self):
        retrieved_data = self.storage.get_compressed_data("nonexistent_key")
        self.assertIsNone(retrieved_data)

    def test_cache_compressed_data(self):
        test_key = "cache_key_1"
        test_payload = "Some heavy string payload to cache efficiently."
        ttl = 60

        self.storage.set_compressed_cache(test_key, test_payload, ttl)
        retrieved_cache = self.storage.get_compressed_cache(test_key)

        self.assertEqual(retrieved_cache, test_payload)

    def test_get_nonexistent_cache(self):
        retrieved_cache = self.storage.get_compressed_cache("nonexistent_cache_key")
        self.assertIsNone(retrieved_cache)

    def test_composition_calls_compressor_and_db(self):
        test_key = "mock_test"
        test_data = {"test": "payload"}

        with patch.object(PayloadCompressor, 'compress_payload', return_value="compressed_mock_string") as mock_compress, \
             patch.object(DBStorage, 'save_data') as mock_save:
            
            self.storage.save_compressed_data(test_key, test_data)
            
            mock_compress.assert_called_once()
            mock_save.assert_called_once_with(test_key, "compressed_mock_string")

    def test_composition_calls_decompressor_and_db(self):
        test_key = "mock_test_get"

        with patch.object(DBStorage, 'get_data', return_value="compressed_mock_string") as mock_get, \
             patch.object(PayloadCompressor, 'decompress_payload', return_value={"test": "payload"}) as mock_decompress:
            
            retrieved = self.storage.get_compressed_data(test_key)
            
            mock_get.assert_called_once_with(test_key)
            mock_decompress.assert_called_once_with("compressed_mock_string")
            self.assertEqual(retrieved, {"test": "payload"})


if __name__ == '__main__':
    unittest.main()