import os
import unittest
from skills.compressed_db_storage import CompressedDBStorage
from skills.db_storage import DBStorage
from skills.payload_compressor import PayloadCompressor

class TestCompressedDBStorageIntegration(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_compressed_storage.db"
        self.storage = CompressedDBStorage(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_save_and_get_compressed_data(self):
        test_key = "test_artifact_key"
        test_data = {"status": "success", "payload": "A" * 1000, "metrics": [1, 2, 3, 4, 5]}

        self.storage.save_data(test_key, test_data)
        retrieved_data = self.storage.get_data(test_key)

        self.assertEqual(retrieved_data, test_data)

    def test_composition_with_underlying_skills(self):
        self.assertIsInstance(self.storage.db, DBStorage)
        self.assertIsInstance(self.storage.compressor, PayloadCompressor)

if __name__ == "__main__":
    unittest.main()