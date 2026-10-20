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
        self.test_dir = f"test_dir_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)

        self.random_metric_val = random.randint(100, 999)
        self.stream_id_val = f"stream_{uuid.uuid4().hex[:8]}"

        self.stability_digest = StabilityDigest()
        self.anomaly_visualizer = AnomalyVisualizer(digest={
            "metric_code": self.random_metric_val,
            "status": "secure"
        })

        self.exporter = DigestExporter(
            stability_digest=self.stability_digest,
            anomaly_visualizer=self.anomaly_visualizer
        )

    def tearDown(self):
        for filename in os.listdir(self.test_dir):
            file_path = os.path.join(self.test_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_export_json_report_integration(self):
        json_filename = f"report_{uuid.uuid4().hex}.json"
        output_path = os.path.join(self.test_dir, json_filename)

        result_path = self.exporter.export_json_report(output_path)

        self.assertTrue(os.path.exists(result_path))
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn('text_report', data)
        self.assertIn('ascii_graph', data)

    def test_export_html_report_integration(self):
        html_filename = f"report_{uuid.uuid4().hex}.html"
        output_path = os.path.join(self.test_dir, html_filename)

        result_path = self.exporter.export_html_report(output_path)

        self.assertTrue(os.path.exists(result_path))
        with open(result_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn("Stability Digest Report", content)

    def test_adapter_json_export_integration(self):
        json_filename = f"adapter_{uuid.uuid4().hex}.json"
        output_path = os.path.join(self.test_dir, json_filename)

        result_path = self.exporter.export_to_json(output_path)

        self.assertTrue(os.path.exists(result_path))
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(data.get("metric_code"), self.random_metric_val)

    def test_adapter_html_export_integration(self):
        html_filename = f"adapter_{uuid.uuid4().hex}.html"
        output_path = os.path.join(self.test_dir, html_filename)

        result_path = self.exporter.export_to_html(output_path)

        self.assertTrue(os.path.exists(result_path))
        with open(result_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn(str(self.random_metric_val), content)

    def test_exporter_error_handling(self):
        invalid_path = os.path.join(self.test_dir, "nonexistent_subfolder", f"{uuid.uuid4().hex}.json")
        with self.assertRaises(DigestExporterError):
            self.exporter.export_json_report(invalid_path)


if __name__ == '__main__':
    unittest.main()