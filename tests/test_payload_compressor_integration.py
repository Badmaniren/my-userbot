import unittest
from skills.payload_compressor import compress_payload, decompress_payload, PayloadCompressorError
from skills.db_storage import DBStorage
from skills.memory_profiler import assert_memory_limit

class TestPayloadCompressorIntegration(unittest.TestCase):
    def setUp(self):
        self.db = DBStorage()

    def test_compress_decompress_string_roundtrip(self):
        original = "Hello, Integration Test for Payload Compressor!"
        compressed = compress_payload(original)
        self.assertIsInstance(compressed, str)
        self.assertNotEqual(compressed, original)
        
        decompressed = decompress_payload(compressed)
        self.assertEqual(decompressed, original)

    def test_compress_decompress_json_roundtrip(self):
        data = {"user": "Inquisitor", "role": "Architect", "permissions": ["read", "write"], "quota": 0}
        compressed = compress_payload(data)
        self.assertIsInstance(compressed, str)
        
        decompressed = decompress_payload(compressed)
        self.assertEqual(decompressed, data)

    def test_storage_integration_with_compression(self):
        large_payload = {"log": "A" * 5000, "status": "critical"}
        compressed = compress_payload(large_payload)
        
        # Save compressed payload into DB storage
        self.db.save_data("test_compressed_key", compressed)
        
        # Retrieve and decompress
        retrieved_compressed = self.db.get_data("test_compressed_key")
        self.assertEqual(retrieved_compressed, compressed)
        
        decompressed = decompress_payload(retrieved_compressed)
        self.assertEqual(decompressed, large_payload)

    def test_memory_profile_during_compression(self):
        heavy_string = "X" * 100000
        assert_memory_limit(100)
        compressed = compress_payload(heavy_string)
        decompressed = decompress_payload(compressed)
        self.assertEqual(decompressed, heavy_string)

    def test_invalid_decompression(self):
        with self.assertRaises((PayloadCompressorError, Exception)):
            decompress_payload("NotABase64String!@#$")

if __name__ == "__main__":
    unittest.main()