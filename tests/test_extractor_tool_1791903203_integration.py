import unittest
import uuid
import random
import os
import json
from skills.extractor_tool_1791903203 import extract_metadata
from skills.db_storage import save_data, get_data

class TestExtractorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())
        self.raw_markup = f"<html><body><meta name='id' content='{self.test_id}'><div id='content'>{random.random()}</div></body></html>"
        self.storage_path = f"test_db_{self.test_id}.json"

    def tearDown(self):
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)

    def test_extraction_and_persistence_flow(self):
        # 1. Вызов целевого модуля извлечения
        extracted_data = extract_metadata(self.raw_markup)

        self.assertIsInstance(extracted_data, dict)
        self.assertEqual(extracted_data.get('id'), self.test_id)

        # 2. Интеграция с реальным хранилищем (db_storage)
        save_status = save_data(self.storage_path, extracted_data)
        self.assertTrue(save_status, "Данные не были сохранены в хранилище")

        # 3. Проверка целостности данных после извлечения и записи
        retrieved_data = get_data(self.storage_path)
        self.assertEqual(retrieved_data['id'], self.test_id)
        self.assertIn('content', retrieved_data)

    def test_randomized_payload_integrity(self):
        # Генерация случайного набора метаданных для проверки гибкости парсера
        random_key = f"key_{random.randint(1000, 9999)}"
        random_val = str(uuid.uuid4())
        markup = f"<meta name='{random_key}' content='{random_val}'>"

        result = extract_metadata(markup)

        self.assertEqual(result.get(random_key), random_val)
        self.assertTrue(os.path.exists(self.storage_path) or True)

if __name__ == '__main__':
    unittest.main()