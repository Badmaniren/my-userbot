import unittest
import uuid
import random
import os
import tempfile
import shutil
from skills.extractor_tool_1793210610 import ExtractorTool
from skills.anomaly_logger import AnomalyLogger

class TestExtractorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.test_dir, f"test_log_{uuid.uuid4().hex}.json")
        self.extractor = ExtractorTool()
        self.logger = AnomalyLogger(self.log_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_extraction_and_logging_integration(self):
        # Генерируем случайные метаданные для разметки
        random_id = uuid.uuid4().hex
        random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        markup = f"<anomaly id='{random_id}' severity='{random_severity}' source='system_test' />"

        # 1. Извлекаем данные через ExtractorTool
        extracted_data = self.extractor.extract(markup)

        # Проверка корректности извлечения
        self.assertEqual(extracted_data.get('id'), random_id)
        self.assertEqual(extracted_data.get('severity'), random_severity)

        # 2. Передаем извлеченные данные в AnomalyLogger (интеграция)
        telemetry_snapshot = {"cpu_load": random.uniform(0, 100), "mem_usage": random.randint(1024, 8192)}
        self.logger.log_anomaly(
            source=extracted_data.get('source', 'unknown'),
            severity=extracted_data.get('severity', 'INFO'),
            details=f"Detected anomaly with ID: {extracted_data.get('id')}",
            telemetry_snapshot=telemetry_snapshot
        )

        # 3. Проверяем, что логгер действительно записал данные
        anomalies = self.logger.get_anomalies()
        self.assertTrue(len(anomalies) > 0)

        found = False
        for entry in anomalies:
            if random_id in entry.get('details', ''):
                found = True
                self.assertEqual(entry.get('severity'), random_severity)
                break

        self.assertTrue(found, "Запись об аномалии не найдена в логах после извлечения")

    def test_parse_attributes_robustness(self):
        # Проверка парсинга случайных атрибутов
        key = f"key_{uuid.uuid4().hex[:5]}"
        val = f"val_{uuid.uuid4().hex[:5]}"
        tag_string = f'{key}="{val}"'

        result = self.extractor.parse_attributes(tag_string)
        self.assertEqual(result.get(key), val)

if __name__ == '__main__':
    unittest.main()