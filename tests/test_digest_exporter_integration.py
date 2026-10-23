import unittest
from unittest.mock import MagicMock
import os
import json
import uuid
import random
from skills.digest_exporter import DigestExporter, DigestExporterError
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.stability_digest import StabilityDigest

class TestDigestExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.rand_suffix = str(uuid.uuid4())[:8]
        self.json_output_path = f"test_report_{self.rand_suffix}.json"
        self.html_output_path = f"test_report_{self.rand_suffix}.html"
        
        self.stability_digest = StabilityDigest(
            repo_path=".",
            anomaly_detector=MagicMock(),
            system_telemetry=MagicMock()
        )
        self.anomaly_visualizer = AnomalyVisualizer()
        
        self.exporter = DigestExporter(
            stability_digest=self.stability_digest,
            anomaly_visualizer=self.anomaly_visualizer
        )

    def tearDown(self):
        for path in [self.json_output_path, self.html_output_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_export_json_report_integration(self):
        random_metric_value = random.randint(100, 999)
        if hasattr(self.anomaly_visualizer, 'digest') and isinstance(self.anomaly_visualizer.digest, dict):
            self.anomaly_visualizer.digest["random_metric"] = random_metric_value

        result_path = self.exporter.export_json_report(self.json_output_path)

        self.assertEqual(result_path, self.json_output_path)
        self.assertTrue(os.path.exists(self.json_output_path))

        with open(self.json_output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("text_report", data)
        self.assertIn("ascii_graph", data)

    def test_export_html_report_integration(self):
        result_path = self.exporter.export_html_report(self.html_output_path)

        self.assertEqual(result_path, self.html_output_path)
        self.assertTrue(os.path.exists(self.html_output_path))

        with open(self.html_output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn("Stability Digest Report", content)

    def test_export_to_json_adapter_integration(self):
        random_key = f"key_{uuid.uuid4().hex[:6]}"
        random_val = random.random()

        if hasattr(self.anomaly_visualizer, 'digest') and isinstance(self.anomaly_visualizer.digest, dict):
            self.anomaly_visualizer.digest[random_key] = random_val

        result_path = self.exporter.export_to_json(self.json_output_path)

        self.assertEqual(result_path, self.json_output_path)
        self.assertTrue(os.path.exists(self.json_output_path))

        with open(self.json_output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn(random_key, data)
        self.assertEqual(data[random_key], random_val)

    def test_export_to_html_adapter_integration(self):
        result_path = self.exporter.export_to_html(self.html_output_path)

        self.assertEqual(result_path, self.html_output_path)
        self.assertTrue(os.path.exists(self.html_output_path))

        with open(self.html_output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn("<body>", content)

    def test_exporter_error_handling(self):
        invalid_path = None
        with self.assertRaises((DigestExporterError, TypeError, OSError)):
            self.exporter.export_json_report(invalid_path)

if __name__ == "__main__":
    unittest.main()