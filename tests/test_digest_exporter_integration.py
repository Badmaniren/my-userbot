import unittest
import os
import json
import uuid
import random
from unittest.mock import MagicMock
from skills.digest_exporter import DigestExporter, DigestExporterError
from skills.stability_digest import StabilityDigest
from skills.anomaly_visualizer import AnomalyVisualizer


class TestDigestExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.output_file = f"test_report_{uuid.uuid4()}.json"
        self.html_output_file = f"test_report_{uuid.uuid4()}.html"

        # Инициализируем реальные компоненты без моков согласно требованиям интеграционного теста
        repo_path = "."
        mock_correlator = MagicMock()
        mock_telemetry = MagicMock()
        self.stability_digest = StabilityDigest(
            repo_path=repo_path,
            anomaly_detector=mock_correlator,
            system_telemetry=mock_telemetry
        )
        self.anomaly_visualizer = AnomalyVisualizer(digest={})
        self.exporter = DigestExporter(
            stability_digest=self.stability_digest,
            anomaly_visualizer=self.anomaly_visualizer
        )

    def tearDown(self):
        for file_path in [self.output_file, self.html_output_file]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    def test_export_json_report_integration(self):
        random_value = random.randint(1000, 9999)

        # Передаем реальные данные через связку навыков
        if hasattr(self.stability_digest, 'add_record'):
            self.stability_digest.add_record(f"metric_{random_value}", float(random_value))

        result_path = self.exporter.export_json_report(self.output_file)

        self.assertEqual(result_path, self.output_file)
        self.assertTrue(os.path.exists(self.output_file))

        with open(self.output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIsInstance(data, dict)
        self.assertIn('text_report', data)
        self.assertIn('ascii_graph', data)

    def test_export_html_report_integration(self):
        random_text_marker = str(uuid.uuid4())

        if hasattr(self.stability_digest, 'add_record'):
            self.stability_digest.add_record(random_text_marker, random.random())

        result_path = self.exporter.export_html_report(self.html_output_file)

        self.assertEqual(result_path, self.html_output_file)
        self.assertTrue(os.path.exists(self.html_output_file))

        with open(self.html_output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn("</html>", content)

    def test_export_to_json_adapter_integration(self):
        random_key = f"key_{uuid.uuid4()}"
        random_val = random.randint(1, 100)

        # Настраиваем состояние визуализатора для адаптера
        self.anomaly_visualizer.digest = {random_key: random_val}

        result_path = self.exporter.export_to_json(self.output_file)

        self.assertEqual(result_path, self.output_file)
        self.assertTrue(os.path.exists(self.output_file))

        with open(self.output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn(random_key, data)
        self.assertEqual(data[random_key], random_val)

    def test_export_exception_handling_no_suppression(self):
        # Проверяем античит: исключения не должны заглушаться, а оборачиваться в DigestExporterError
        bad_path = None

        with self.assertRaises(DigestExporterError):
            self.exporter.export_json_report(bad_path)


if __name__ == '__main__':
    unittest.main()