import unittest
import uuid
import random
import os
from skills.extractor_tool_1790094708 import ExtractorTool

class TestExtractorToolIntegration(unittest.TestCase):
    def setUp(self):
        self.tool = ExtractorTool()
        self.random_id = str(uuid.uuid4())
        self.random_metric = random.uniform(0.001, 999.999)
        self.random_tag = f"tag_{random.randint(1000, 9999)}"

        # Формируем динамическую разметку для извлечения
        self.markup_data = f"""
        <root>
            <metadata>
                <entry key="trace_id" value="{self.random_id}" />
                <entry key="metric_val" value="{self.random_metric}" />
                <entry key="label" value="{self.random_tag}" />
            </metadata>
        </root>
        """

    def test_extraction_integration_flow(self):
        # Вызываем основной метод модуля для извлечения метаданных
        # Без использования моков, проверяем реальное взаимодействие компонентов внутри модуля
        result = self.tool.extract_metadata_from_markup(self.markup_data)

        # Проверка корректности извлечения случайных данных
        self.assertIsNotNone(result, "Результат извлечения не должен быть пустым")
        self.assertEqual(result.get("trace_id"), self.random_id, "UUID должен совпадать с входным случайным значением")
        self.assertEqual(float(result.get("metric_val")), self.random_metric, "Метрика должна совпадать")
        self.assertEqual(result.get("label"), self.random_tag, "Тег должен соответствовать сгенерированному")

        # Проверка системных атрибутов, которые генерирует модуль (интеграционный след)
        self.assertIn("processing_timestamp", result)
        self.assertIn("extractor_version", result)

    def test_extraction_persistence_and_id_generation(self):
        # Проверяем, что модуль генерирует уникальный ID операции и он не статичен
        result_1 = self.tool.extract_metadata_from_markup(self.markup_data)
        result_2 = self.tool.extract_metadata_from_markup(self.markup_data)

        op_id_1 = result_1.get("operation_id")
        op_id_2 = result_2.get("operation_id")

        self.assertIsNotNone(op_id_1)
        self.assertIsNotNone(op_id_2)
        self.assertNotEqual(op_id_1, op_id_2, "ID операций должны быть уникальными для каждого вызова")

    def test_file_artifact_creation(self):
        # Если модуль по логике должен создавать временный лог или кэш (согласно описанию системы)
        # Проверяем реальное появление артефакта на диске с использованием случайного префикса
        test_prefix = f"test_run_{random.randint(1, 100000)}"
        artifact_path = self.tool.generate_extraction_report(self.markup_data, prefix=test_prefix)

        try:
            self.assertTrue(os.path.exists(artifact_path), f"Файл отчета {artifact_path} должен быть создан")
            with open(artifact_path, 'r') as f:
                content = f.read()
                self.assertIn(self.random_id, content, "Случайный ID должен присутствовать в созданном файле")
        finally:
            if os.path.exists(artifact_path):
                os.remove(artifact_path)

if __name__ == "__main__":
    unittest.main()
