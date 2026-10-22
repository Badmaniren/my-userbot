import unittest
import os
import json
import uuid
import random
from skills.stability_digest import StabilityDigest
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.json_output_path = os.path.join(self.test_dir, f"test_report_{self.rand_suffix}.json")
        self.html_output_path = os.path.join(self.test_dir, f"test_report_{self.rand_suffix}.html")
        
        self.random_metric_val = random.randint(100, 999)
        self.random_stream_id = f"stream_{uuid.uuid4().hex[:6]}"

        self.stability_digest = StabilityDigest(
            repo_path=self.test_dir,
            anomaly_detector=None,
            system_telemetry=None
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
        result_path = self.exporter.export_json_report(self.json_output_path)

        self.assertEqual(result_path, self.json_output_path)
        self.assertTrue(os.path.exists(self.json_output_path))

        with open(self.json_output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIsInstance(data, dict)
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
        result_path = self.exporter.export_to_json(self.json_output_path)

        self.assertEqual(result_path, self.json_output_path)
        self.assertTrue(os.path.exists(self.json_output_path))

        with open(self.json_output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIsInstance(data, dict)

    def test_export_to_html_adapter_integration(self):
        result_path = self.exporter.export_to_html(self.html_output_path)

        self.assertEqual(result_path, self.html_output_path)
        self.assertTrue(os.path.exists(self.html_output_path))

        with open(self.html_output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("<html><body><pre>", content)


if __name__ == "__main__":
    unittest.main()