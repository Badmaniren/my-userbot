import unittest
import uuid
import random
import os
from skills.incident_digest_generator import generate_incident_digest
from skills.incident_aggregator import aggregate_incidents
from skills.system_health_aggregator import get_aggregated_health_data

class TestIncidentDigestIntegration(unittest.TestCase):
    def setUp(self):
        self.test_run_id = str(uuid.uuid4())
        self.incident_count = random.randint(3, 10)
        self.output_path = f"digest_{self.test_run_id}.txt"

    def tearDown(self):
        if os.path.exists(self.output_path):
            os.remove(self.output_path)

    def test_digest_generation_flow(self):
        # 1. Получаем сырые данные через системный агрегатор
        raw_health_data = get_aggregated_health_data(source_id=self.test_run_id)
        
        # 2. Агрегируем инциденты (интеграция с incident_aggregator)
        incidents = aggregate_incidents(
            health_data=raw_health_data, 
            limit=self.incident_count
        )
        
        # 3. Генерируем отчет (целевой модуль)
        result = generate_incident_digest(
            incidents=incidents,
            output_file=self.output_path,
            metadata={"request_id": self.test_run_id}
        )

        # Проверка возвращаемых значений
        self.assertIn("status", result)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["request_id"], self.test_run_id)

        # Проверка реальных изменений в файловой системе
        self.assertTrue(os.path.exists(self.output_path), "Файл отчета не был создан")
        
        with open(self.output_path, 'r') as f:
            content = f.read()
            self.assertIn(self.test_run_id, content, "ID запроса отсутствует в сгенерированном отчете")
            self.assertGreater(len(content), 0, "Файл отчета пуст")

if __name__ == '__main__':
    unittest.main()