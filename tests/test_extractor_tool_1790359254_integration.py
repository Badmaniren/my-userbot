import unittest
import uuid
import random
import os
import json
from skills.extractor_tool_1790359254 import extract_metadata
from skills.db_storage import save_record, get_record

class TestExtractorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())
        self.test_payload = {
            "id": self.test_id,
            "content": f"Market analysis data point {random.randint(1000, 9999)}",
            "timestamp": random.random()
        }
        self.temp_file = f"temp_markup_{self.test_id}.json"
        with open(self.temp_file, 'w') as f:
            json.dump(self.test_payload, f)

    def tearDown(self):
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)

    def test_metadata_extraction_and_persistence_flow(self):
        # Вызов целевого модуля
        metadata = extract_metadata(self.temp_file)

        # Проверка корректности извлечения
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['id'], self.test_id)

        # Интеграция с db_storage без моков
        save_result = save_record("metadata_store", metadata)
        self.assertTrue(save_result, "Database storage failed to persist metadata")

        # Проверка реального состояния в БД
        retrieved_data = get_record("metadata_store", self.test_id)
        self.assertIsNotNone(retrieved_data)
        self.assertEqual(retrieved_data['id'], self.test_id)
        self.assertEqual(retrieved_data['content'], self.test_payload['content'])

if __name__ == '__main__':
    unittest.main()
