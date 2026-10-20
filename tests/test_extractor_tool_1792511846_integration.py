import os
import random
import shutil
import unittest
import uuid

from skills.extractor_tool_1792511846 import ExtractorTool

try:
    from skills.git_inspector import GitInspector
    from skills.anomaly_logger import AnomalyLogger
except ImportError:
    from git_inspector import GitInspector
    from anomaly_logger import AnomalyLogger


class TestExtractorToolIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = f"test_repo_{uuid.uuid4().hex}"
        os.makedirs(cls.test_dir)
        cls.log_path = f"anomaly_{uuid.uuid4().hex}.log"

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
        if os.path.exists(cls.log_path):
            os.remove(cls.log_path)

    def test_extraction_and_logging_flow(self):
        # 1. Подготовка окружения через GitInspector
        inspector = GitInspector(repo_path=self.test_dir)
        test_file = os.path.join(self.test_dir, "test_markup.txt")
        random_content = f"METADATA_ID:{uuid.uuid4()} | SEVERITY:{random.choice(['LOW', 'HIGH'])}"

        with open(test_file, "w") as f:
            f.write(random_content)

        # 2. Инициализация тестируемого модуля
        extractor = ExtractorTool()

        # 3. Выполнение извлечения
        extracted_data = extractor.extract(test_file)
        self.assertIsNotNone(extracted_data)
        self.assertIn("METADATA_ID", extracted_data)

        # 4. Интеграция с AnomalyLogger для фиксации результата
        logger = AnomalyLogger(log_path=self.log_path)
        source_id = f"extractor_{uuid.uuid4().hex}"

        logger.log_anomaly(
            source=source_id,
            severity="INFO",
            details=str(extracted_data),
            telemetry_snapshot={"file": test_file}
        )

        # 5. Проверка целостности данных (реальное чтение лога)
        report = logger.get_anomalies()
        found = False
        for entry in report:
            if entry.get('source') == source_id:
                found = True
                self.assertEqual(entry.get('details'), str(extracted_data))

        self.assertTrue(found, "Данные из ExtractorTool не были корректно залогированы в AnomalyLogger")

    def test_empty_extraction_behavior(self):
        # Проверка обработки пустого файла
        empty_file = os.path.join(self.test_dir, f"empty_{uuid.uuid4().hex}.txt")
        with open(empty_file, "w") as f:
            f.write("")

        extractor = ExtractorTool()
        result = extractor.extract(empty_file)

        # Ожидаем, что модуль вернет пустой словарь или None, но не упадет
        self.assertIsInstance(result, (dict, type(None)))


if __name__ == '__main__':
    unittest.main()
