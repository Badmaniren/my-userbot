import unittest
import uuid
import random
import os
import json
from skills.extractor_tool_1790625955 import extractor_tool_1790625955
try:
    from skills.db_storage import db_storage
except ImportError:
    from db_storage import db_storage

class TestExtractorToolIntegration(unittest.TestCase):
    def setUp(self):
        self.storage = db_storage()
        self.test_id = str(uuid.uuid4())
        self.raw_markup = f"<html><body><div id='{self.test_id}'>Test Content {random.randint(1000, 9999)}</div></body></html>"
        self.test_file_path = f"test_data_{self.test_id}.html"

        with open(self.test_file_path, "w") as f:
            f.write(self.raw_markup)

    def tearDown(self):
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_metadata_extraction_flow(self):
        # Вызов целевого модуля
        result = extractor_tool_1790625955(file_path=self.test_file_path, record_id=self.test_id)

        # Проверка возвращаемых данных
        self.assertIsNotNone(result, "Модуль не вернул результат")
        self.assertEqual(result.get("id"), self.test_id, "ID в метаданных не совпадает с переданным")

        # Проверка записи в реальное хранилище (интеграция)
        stored_data = self.storage.get_record(self.test_id)
        self.assertIsNotNone(stored_data, "Данные не были сохранены в db_storage")
        self.assertEqual(stored_data.get("status"), "processed")

        # Проверка консистентности данных
        self.assertIn("content_hash", result)
        self.assertTrue(len(result.get("content_hash")) > 0)

if __name__ == "__main__":
    unittest.main()