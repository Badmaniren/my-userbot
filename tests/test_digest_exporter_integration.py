import unittest
import os
import json
import uuid
import random
import tempfile
import shutil
from skills.digest_exporter import DigestExporter, DigestExporterError
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.stability_digest import StabilityDigest

class TestDigestExporterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_working_dir = tempfile.mkdtemp()

        # Инициализация реальных объектов без моков
        self.stability_digest = StabilityDigest()
        self.anomaly_visualizer = AnomalyVisualizer()

        # Настройка состояния для визуализатора (имитация реальных данных через атрибуты)
        # Так как это интеграционный тест, мы проверяем как DigestExporter взаимодействует с состоянием этих объектов
        self.random_payload = {
            "session_id": str(uuid.uuid4()),
            "anomaly_count": random.randint(1, 100),
            "risk_level": random.choice(["low", "medium", "high", "critical"])
        }
        self.anomaly_visualizer.digest = self.random_payload

        self.exporter = DigestExporter(
            stability_digest=self.stability_digest,
            anomaly_visualizer=self.anomaly_visualizer
        )

    def tearDown(self):
        if os.path.exists(self.test_working_dir):
            shutil.rmtree(self.test_working_dir)

    def test_full_json_report_export_flow(self):
        """Интеграционная проверка экспорта JSON отчета с реальными зависимостями."""
        report_name = f"report_{uuid.uuid4().hex}.json"
        output_path = os.path.join(self.test_working_dir, report_name)

        result_path = self.exporter.export_json_report(output_path)

        self.assertEqual(result_path, output_path)
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Проверяем структуру, которую генерирует AnomalyVisualizer внутри DigestExporter
            self.assertIn('text_report', data)
            self.assertIn('ascii_graph', data)
            self.assertIsInstance(data['text_report'], str)

    def test_html_report_generation_persistence(self):
        """Проверка создания HTML файла и наличия в нем динамических данных."""
        report_name = f"index_{uuid.uuid4().hex}.html"
        output_path = os.path.join(self.test_working_dir, report_name)

        result_path = self.exporter.export_html_report(output_path)

        self.assertTrue(os.path.exists(result_path))
        with open(result_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("<html>", content)
            self.assertIn("Stability Digest Report", content)
            # Проверяем, что визуализатор отработал и вставил данные
            self.assertIn("Metrics", content)

    def test_export_stream_to_json_integration(self):
        """Проверка взаимодействия с StabilityDigest для экспорта потока."""
        stream_id = f"sid_{uuid.uuid4().hex}"
        file_name = f"stream_{uuid.uuid4().hex}.json"
        output_path = os.path.join(self.test_working_dir, file_name)

        # Вызов метода, который внутри обращается к self.digest.export_digest_stream
        try:
            result_path = self.exporter.export_stream_to_json(stream_id, output_path)

            self.assertTrue(os.path.exists(result_path))
            with open(result_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.assertIsInstance(data, (dict, list))
        except Exception as e:
            # Если StabilityDigest требует предварительной регистрации stream_id,
            # тест покажет реальную ошибку интеграции
            self.fail(f"Export stream failed during integration: {e}")

    def test_adapter_methods_with_random_data(self):
        """Тестирование методов-адаптеров на корректность передачи данных из visualizer.digest."""
        json_path = os.path.join(self.test_working_dir, f"adapter_{uuid.uuid4().hex}.json")
        html_path = os.path.join(self.test_working_dir, f"adapter_{uuid.uuid4().hex}.html")

        # Тест JSON адаптера
        self.exporter.export_to_json(json_path)
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data["session_id"], self.random_payload["session_id"])
            self.assertEqual(data["risk_level"], self.random_payload["risk_level"])

        # Тест HTML адаптера
        self.exporter.export_to_html(html_path)
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(self.random_payload["session_id"], content)

    def test_error_handling_invalid_path(self):
        """Проверка генерации DigestExporterError при системных ошибках (неверный путь)."""
        invalid_path = "/non_existent_directory/report.json"

        with self.assertRaises(DigestExporterError):
            self.exporter.export_json_report(invalid_path)

if __name__ == '__main__':
    unittest.main()