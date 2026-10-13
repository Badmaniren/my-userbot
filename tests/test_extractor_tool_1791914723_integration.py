import unittest
import uuid
import random
import string
from skills.extractor_tool_1791914723 import extract_metadata_from_markup
from skills.db_storage import db_storage

class TestExtractorToolIntegration(unittest.TestCase):
    def setUp(self):
        self.test_session_id = f"session_{uuid.uuid4().hex[:8]}"

    def generate_random_markup(self, target_id, target_value):
        tags = ["item", "node", "entry", "data"]
        random_tag = random.choice(tags)
        noise = "".join(random.choices(string.ascii_letters, k=15))
        return f"""
        <root>
            <metadata>
                <id>{target_id}</id>
                <value>{target_value}</value>
                <noise>{noise}</noise>
            </metadata>
            <context>
                <session>{self.test_session_id}</session>
            </context>
        </root>
        """

    def test_full_extraction_and_storage_flow(self):
        # Генерируем случайные входные данные
        random_uuid = str(uuid.uuid4())
        random_payload = "payload_" + "".join(random.choices(string.ascii_uppercase + string.digits, k=12))
        
        markup = self.generate_random_markup(random_uuid, random_payload)
        
        # Вызов тестируемого модуля (интеграция с парсером внутри)
        # Модуль должен вернуть структурированный словарь
        result = extract_metadata_from_markup(markup)
        
        # Проверка возвращаемого значения
        self.assertIsInstance(result, dict, "Результат должен быть словарем")
        self.assertEqual(result.get("id"), random_uuid, f"Ожидался UUID {random_uuid}, получено {result.get('id')}")
        self.assertEqual(result.get("value"), random_payload, "Метаданные payload не совпадают")
        
        # Проверка интеграции с db_storage (реальное изменение в БД)
        # Предполагаем, что экстрактор сохраняет результат под ключом UUID
        stored_data = db_storage.get_record(random_uuid)
        
        self.assertIsNotNone(stored_data, "Запись не была найдена в db_storage после экстракции")
        self.assertEqual(stored_data.get("session_id"), self.test_session_id)
        self.assertEqual(stored_data.get("extracted_value"), random_payload)

    def test_extraction_with_malformed_random_data(self):
        # Проверка устойчивости на случайном мусоре
        garbage_input = "".join(random.choices(string.printable, k=100))
        
        # Модуль должен корректно обрабатывать ошибки без падения
        result = extract_metadata_from_markup(garbage_input)
        
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertFalse(result.get("success", True))

if __name__ == "__main__":
    unittest.main()