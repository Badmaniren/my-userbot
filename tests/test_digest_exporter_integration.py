import unittest
import os
import json
import uuid
import random
from skills.digest_exporter import DigestExporter, DigestExporterError
from skills.stability_digest import StabilityDigest
from skills.anomaly_visualizer import AnomalyVisualizer


class TestDigestExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.output_json = f"test_report_{uuid.uuid4()}.json"
        self.output_html = f"test_report_{uuid.uuid4()}.html"
        self.stream_json = f"test_stream_{uuid.uuid4()}.json"
        self.files_to_cleanup = [self.output_json, self.output_html, self.stream_json]

        self.stability_digest = StabilityDigest()
        self.anomaly_visualizer = AnomalyVisualizer()
        self.exporter = DigestExporter(
            stability_digest=self.stability_digest,
            anomaly_visualizer=self.anomaly_visualizer
        )

    def tearDown(self):
        for file_path in self.files_to_cleanup:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    def test_export_json_report_integration(self):
        random_metric_val = random.randint(100, 999)
        if hasattr(self.anomaly_visualizer, 'digest') and isinstance(self.anomaly_visualizer.digest, dict):
            self.anomaly_visualizer.digest["integration_metric"] = random_metric_val

        result_path = self.exporter.export_json_report(self.output_json)
        
        self.assertEqual(result_path, self.output_json)
        self.assertTrue(os.path.exists(self.output_json))

        with open(self.output_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertIsInstance(data, dict)
            self.assertIn("text_report", data)
            self.assertIn("ascii_graph", data)

    def test_export_html_report_integration(self):
        result_path = self.exporter.export_html_report(self.output_html)

        self.assertEqual(result_path, self.output_html)
        self.assertTrue(os.path.exists(self.output_html))

        with open(self.output_html, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("<html>", content)
            self.assertIn("Stability Digest Report", content)

    def test_export_to_json_adapter_integration(self):
        random_key = f"key_{uuid.uuid4().hex[:6]}"
        random_val = random.randint(1, 10000)

        if hasattr(self.anomaly_visualizer, 'digest') and isinstance(self.anomaly_visualizer.digest, dict):
            self.anomaly_visualizer.digest[random_key] = random_val

        result_path = self.exporter.export_to_json(self.output_json)

        self.assertEqual(result_path, self.output_json)
        self.assertTrue(os.path.exists(self.output_json))

        with open(self.output_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertIsInstance(data, dict)
            if random_key in data:
                self.assertEqual(data[random_key], random_val)

    def test_export_to_html_adapter_integration(self):
        result_path = self.exporter.export_to_html(self.output_html)

        self.assertEqual(result_path, self.output_html)
        self.assertTrue(os.path.exists(self.output_html))

        with open(self.output_html, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("<html><body><pre>", content)


if __name__ == "__main__":
    unittest.main()