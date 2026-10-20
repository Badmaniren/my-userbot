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
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.json_output_path = os.path.join(self.test_dir, f"test_report_{self.rand_suffix}.json")
        self.html_output_path = os.path.join(self.test_dir, f"test_report_{self.rand_suffix}.html")

        self.stability_digest = StabilityDigest()
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
        random_metric_val = random.randint(100, 999)
        self.anomaly_visualizer.digest = {"integration_metric": random_metric_val, "status": "stable"}

        result_path = self.exporter.export_json_report(self.json_output_path)

        self.assertEqual(result_path, self.json_output_path)
        self.assertTrue(os.path.exists(self.json_output_path))

        with open(self.json_output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn("integration_metric", data)
        self.assertEqual(data["integration_metric"], random_metric_val)
        self.assertIn("text_report", data)
        self.assertIn("ascii_graph", data)

    def test_export_html_report_integration(self):
        random_status_val = f"status_code_{random.randint(1000, 9999)}"
        self.anomaly_visualizer.digest = {"check_key": random_status_val}

        result_path = self.exporter.export_html_report(self.html_output_path)

        self.assertEqual(result_path, self.html_output_path)
        self.assertTrue(os.path.exists(self.html_output_path))

        with open(self.html_output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn("Stability Digest Report", content)
        self.assertIn(random_status_val, content)

    def test_adapters_json_and_html_integration(self):
        random_anomaly_id = f"anomaly-{uuid.uuid4().hex[:6]}"
        self.anomaly_visualizer.digest = {"anomaly_id": random_anomaly_id, "severity": "HIGH"}

        json_res = self.exporter.export_to_json(self.json_output_path)
        html_res = self.exporter.export_to_html(self.html_output_path)

        self.assertTrue(os.path.exists(json_res))
        self.assertTrue(os.path.exists(html_res))

        with open(json_res, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            self.assertEqual(json_data.get("anomaly_id"), random_anomaly_id)

        with open(html_res, 'r', encoding='utf-8') as f:
            html_data = f.read()
            self.assertIn(random_anomaly_id, html_data)

    def test_exporter_error_handling(self):
        invalid_path = os.path.join("/nonexistent_dir_12345", f"fail_{uuid.uuid4().hex}.json")
        with self.assertRaises(DigestExporterError):
            self.exporter.export_json_report(invalid_path)


if __name__ == '__main__':
    unittest.main()