import unittest
import os
import json
import uuid
import random
from skills.digest_exporter import DigestExporter, DigestExporterError
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.stability_digest import StabilityDigest

class TestDigestExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.output_json = f"test_report_{uuid.uuid4()}.json"
        self.output_html = f"test_report_{uuid.uuid4()}.html"
        self.stream_id = str(uuid.uuid4())
        
        self.visualizer = AnomalyVisualizer()
        self.digest = StabilityDigest()
        self.exporter = DigestExporter(stability_digest=self.digest, anomaly_visualizer=self.visualizer)

    def tearDown(self):
        for path in [self.output_json, self.output_html]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_export_json_report_integration(self):
        random_metric_val = random.randint(100, 999)
        if hasattr(self.visualizer, "digest") and isinstance(self.visualizer.digest, dict):
            self.visualizer.digest["random_metric"] = random_metric_val

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
            self.assertIn("Digest Report", content)

    def test_export_to_json_integration(self):
        random_key = f"key_{uuid.uuid4().hex[:6]}"
        random_val = random.random()

        if not hasattr(self.visualizer, "digest") or not isinstance(self.visualizer.digest, dict):
            self.visualizer.digest = {}
        self.visualizer.digest[random_key] = random_val

        result_path = self.exporter.export_to_json(self.output_json)

        self.assertEqual(result_path, self.output_json)
        self.assertTrue(os.path.exists(self.output_json))

        with open(self.output_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertIn(random_key, data)
            self.assertEqual(data[random_key], random_val)

    def test_export_to_html_integration(self):
        result_path = self.exporter.export_to_html(self.output_html)

        self.assertEqual(result_path, self.output_html)
        self.assertTrue(os.path.exists(self.output_html))

        with open(self.output_html, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("<html>", content)
            self.assertIn("<body>", content)

    def test_export_stream_to_json_error_handling(self):
        invalid_stream_id = f"nonexistent_{uuid.uuid4()}"
        with self.assertRaises(DigestExporterError):
            self.exporter.export_stream_to_json(invalid_stream_id, self.output_json)

if __name__ == "__main__":
    unittest.main()