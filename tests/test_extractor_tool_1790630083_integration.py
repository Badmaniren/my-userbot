import os
import sys
import uuid
import random
import unittest

# Add root directory and skills directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from skills.extractor_tool_1790630083 import extract_metadata
try:
    from skills.db_storage import save_record, get_record
except ImportError:
    from db_storage import save_record, get_record


class TestExtractorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())
        self.test_content = f"<html><body><meta name='ticker' content='{self.test_id}'><p>Data {random.random()}</p></body></html>"
        self.storage_path = f"test_db_{self.test_id}.json"

    def tearDown(self):
        if os.path.exists(self.storage_path):
            try:
                os.remove(self.storage_path)
            except OSError:
                pass

    def test_metadata_extraction_and_persistence_flow(self):
        # 1. Вызов модуля извлечения
        extracted_data = extract_metadata(self.test_content)

        # Проверка корректности извлечения случайного ID
        self.assertIsNotNone(extracted_data)
        self.assertEqual(extracted_data.get('ticker'), self.test_id)

        # 2. Интеграция с реальным хранилищем (db_storage)
        save_status = save_record(self.storage_path, extracted_data)
        self.assertTrue(save_status, "Данные не были сохранены в хранилище")

        # 3. Верификация через чтение из хранилища
        retrieved_data = get_record(self.storage_path, self.test_id)

        self.assertIsNotNone(retrieved_data, "Данные не найдены в хранилище после записи")
        self.assertEqual(retrieved_data['ticker'], self.test_id)
        self.assertEqual(retrieved_data, extracted_data, "Данные в хранилище не совпадают с извлеченными")

    def test_empty_input_handling(self):
        random_empty_id = str(uuid.uuid4())
        empty_content = "<html></html>"

        extracted = extract_metadata(empty_content)

        # Проверка, что модуль корректно обрабатывает отсутствие метаданных
        self.assertIsInstance(extracted, dict)
        self.assertNotIn('ticker', extracted)


if __name__ == '__main__':
    unittest.main()
