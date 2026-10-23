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
        self.stream_id = f"stream_{uuid.uuid4()}"
        
        self.stability_digest = StabilityDigest()
        self.anomaly_visualizer = AnomalyVisualizer(digest={
            "metric_key": f"value_{uuid.uuid4()}",
            "random_score": random.randint(1, 100)
        })
        
        self.exporter = DigestExporter(
            stability_digest=self.stability_digest,
            anomaly_visualizer=self.anomaly_visualizer
        )

    def tearDown(self):
        for path in [self.output_json, self.output_html]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_export_json_report_integration(self):
        result_path = self.exporter.export_json_report(self.output_json)
        self.assertEqual(result_path, self.output_json)
        self.assertTrue(os.path.exists(self.output_json))

        with open(self.output_json, "r", encoding="utf-8") as f:
            data = json.load(f)
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

    def test_export_to_json_integration(self):
        result_path = self.exporter.export_to_json(self.output_json)
        self.assertEqual(result_path, self.output_json)
        self.assertTrue(os.path.exists(self.output_json))

        with open(self.output_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertIsInstance(data, dict)

    def test_export_to_html_integration(self):
        result_path = self.exporter.export_to_html(self.output_html)
        self.assertEqual(result_path, self.output_html)
        self.assertTrue(os.path.exists(self.output_html))

        with open(self.output_html, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("<html>", content)

    def test_exporter_error_handling(self):
        bad_exporter = DigestExporter(stability_digest=None, anomaly_visualizer=None)
        with self.assertRaises(DigestExporterError):
            bad_exporter.export_json_report(self.output_json)


if __name__ == "__main__":
    unittest.main()