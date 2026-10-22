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
        self.json_output_path = os.path.join(self.test_dir, f"test_report_{uuid.uuid4()}.json")
        self.html_output_path = os.path.join(self.test_dir, f"test_report_{uuid.uuid4()}.html")
        
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
        self.anomaly_visualizer.digest = {"security_score": random_metric_val, "status": "stable"}

        result_path = self.exporter.export_json_report(self.json_output_path)

        self.assertEqual(result_path, self.json_output_path)
        self.assertTrue(os.path.exists(self.json_output_path))

        with open(self.json_output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("text_report", data)
        self.assertIn("ascii_graph", data)

    def test_export_html_report_integration(self):
        random_metric_val = random.randint(1000, 9999)
        self.anomaly_visualizer.digest = {"anomaly_count": random_metric_val}

        result_path = self.exporter.export_html_report(self.html_output_path)

        self.assertEqual(result_path, self.html_output_path)
        self.assertTrue(os.path.exists(self.html_output_path))

        with open(self.html_output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn("Digest Report", content)

    def test_export_to_json_adapter(self):
        random_id = str(uuid.uuid4())
        self.anomaly_visualizer.digest = {"unique_run_id": random_id}

        result_path = self.exporter.export_to_json(self.json_output_path)

        self.assertEqual(result_path, self.json_output_path)
        self.assertTrue(os.path.exists(self.json_output_path))

        with open(self.json_output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("unique_run_id"), random_id)

    def test_export_to_html_adapter(self):
        random_token = uuid.uuid4().hex
        self.anomaly_visualizer.digest = {"auth_token": random_token}

        result_path = self.exporter.export_to_html(self.html_output_path)

        self.assertEqual(result_path, self.html_output_path)
        self.assertTrue(os.path.exists(self.html_output_path))

        with open(self.html_output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(random_token, content)
        self.assertIn("<html>", content)

    def test_exporter_exception_handling(self):
        invalid_path = os.path.join("/non_existent_restricted_folder_12345", f"fail_{uuid.uuid4()}.json")

        with self.assertRaises(DigestExporterError):
            self.exporter.export_to_json(invalid_path)


if __name__ == "__main__":
    unittest.main()