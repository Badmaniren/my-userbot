import unittest
import os
import tempfile
import uuid
import random
from skills.digest_exporter import DigestExporter
from skills.stability_digest import StabilityDigest
from skills.anomaly_visualizer import AnomalyVisualizer

class TestDigestExporterIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self.execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        self.random_metric_value = random.uniform(10.0, 100.0)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_digest_exporter_integration_workflow(self):
        # 1. Создаем реальные зависимости без моков
        stability_digest_instance = StabilityDigest(
            repo_path=self.repo_path,
            anomaly_detector=None,
            system_telemetry=None
        )

        # Генерируем реальный дайджест через связанный модуль
        digest_data = stability_digest_instance.generate_digest(execution_id=self.execution_id)
        
        # Инъецируем случайные данные для проверки сквозной передачи
        if isinstance(digest_data, dict):
            digest_data["random_test_metric"] = self.random_metric_value

        # 2. Инициализируем визуализатор (обязательная композиция)
        visualizer = AnomalyVisualizer(digest=digest_data)

        # 3. Создаем целевой модуль экспорта
        exporter = DigestExporter(visualizer=visualizer, stability_digest=stability_digest_instance)

        # Пути для экспорта отчетов с использованием случайных имен файлов
        json_filename = f"report_{uuid.uuid4().hex}.json"
        html_filename = f"report_{uuid.uuid4().hex}.html"
        json_path = os.path.join(self.repo_path, json_filename)
        html_path = os.path.join(self.repo_path, html_filename)

        # 4. Выполняем реальный экспорт через тестируемый модуль
        exported_json = exporter.export_to_json(json_path)
        exported_html = exporter.export_to_html(html_path)

        # 5. Проверяем реальные изменения и артефакты на диске
        self.assertTrue(os.path.exists(json_path), "JSON файл отчета не был создан на диске.")
        self.assertTrue(os.path.exists(html_path), "HTML файл отчета не был создан на диске.")

        # Проверяем, что файлы не пустые
        self.assertGreater(os.path.getsize(json_path), 0, "JSON файл отчета пуст.")
        self.assertGreater(os.path.getsize(html_path), 0, "HTML файл отчета пуст.")

        # Проверяем сохранение целостности данных (случайный execution_id и метрика дошли до экспорта)
        with open(json_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
            self.assertIn(str(self.execution_id), file_content, "Случайный execution_id не найден в экспортированном JSON.")
            self.assertIn(str(self.random_metric_value), file_content, "Случайная метрика не найдена в экспортированном JSON.")

        # Проверяем возвращаемые значения методов экспорта
        self.assertEqual(exported_json, json_path)
        self.assertEqual(exported_html, html_path)

if __name__ == '__main__':
    unittest.main()