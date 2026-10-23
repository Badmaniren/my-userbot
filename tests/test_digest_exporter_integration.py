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
        self.output_json_path = f"test_report_{uuid.uuid4()}.json"
        self.output_html_path = f"test_report_{uuid.uuid4()}.html"
        self.stream_id = str(uuid.uuid4())
        
        self.stability_digest = StabilityDigest()
        self.anomaly_visualizer = AnomalyVisualizer()
        self.exporter = DigestExporter(
            stability_digest=self.stability_digest,
            anomaly_visualizer=self.anomaly_visualizer
        )

    def tearDown(self):
        for path in [self.output_json_path, self.output_html_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_export_json_report_integration(self):
        result_path = self.exporter.export_json_report(self.output_json_path)

        self.assertEqual(result_path, self.output_json_path)
        self.assertTrue(os.path.exists(self.output_json_path))

        with open(self.output_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIsInstance(data, dict)
        self.assertIn("text_report", data)
        self.assertIn("ascii_graph", data)

    def test_export_html_report_integration(self):
        result_path = self.exporter.export_html_report(self.output_html_path)

        self.assertEqual(result_path, self.output_html_path)
        self.assertTrue(os.path.exists(self.output_html_path))

        with open(self.output_html_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn("Stability Digest Report", content)

    def test_export_stream_to_json_integration(self):
        try:
            result_path = self.exporter.export_stream_to_json(self.stream_id, self.output_json_path)
            self.assertEqual(result_path, self.output_json_path)
            self.assertTrue(os.path.exists(self.output_json_path))
        except Exception as e:
            self.assertIsInstance(e, DigestExporterError)

    def test_export_to_json_adapter(self):
        self.anomaly_visualizer.digest = {"random_metric": random.randint(100, 999)}

        result_path = self.exporter.export_to_json(self.output_json_path)

        self.assertEqual(result_path, self.output_json_path)
        self.assertTrue(os.path.exists(self.output_json_path))

        with open(self.output_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("random_metric"), self.anomaly_visualizer.digest["random_metric"])

    def test_export_to_html_adapter(self):
        self.anomaly_visualizer.digest = {"random_status": f"status_{uuid.uuid4()}"}

        result_path = self.exporter.export_to_html(self.output_html_path)

        self.assertEqual(result_path, self.output_html_path)
        self.assertTrue(os.path.exists(self.output_html_path))

        with open(self.output_html_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn(self.anomaly_visualizer.digest["random_status"], content)


if __name__ == "__main__":
    unittest.main()