import unittest
import os
import json
import uuid
import random
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.stability_digest import StabilityDigest
from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = f"test_dir_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        
        self.json_output_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.json")
        self.html_output_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.html")
        self.md_output_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.md")

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
        for path in [self.json_output_path, self.html_output_path, self.md_output_path]:
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_export_json_report_integration(self):
        random_metric_val = random.randint(100, 999)
        self.anomaly_visualizer.digest = {"metric_stability": random_metric_val}

        result_path = self.exporter.export_json_report(self.json_output_path)

        self.assertEqual(result_path, self.json_output_path)
        self.assertTrue(os.path.exists(self.json_output_path))

        with open(self.json_output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("text_report", data)
        self.assertIn("ascii_graph", data)

    def test_export_html_report_integration(self):
        random_metric_val = random.randint(1000, 9999)
        self.anomaly_visualizer.digest = {"stability_score": random_metric_val}

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

        self.anomaly_visualizer.digest = {random_key: random_val}

        result_path = self.exporter.export_to_json(self.json_output_path)

        self.assertEqual(result_path, self.json_output_path)
        self.assertTrue(os.path.exists(self.json_output_path))

        with open(self.json_output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn(random_key, data)
        self.assertEqual(data[random_key], random_val)

    def test_export_markdown_report_integration(self):
        random_metric_val = random.randint(100, 999)
        self.anomaly_visualizer.digest = {"metric_stability": random_metric_val}

        result_path = self.exporter.export_markdown_report(self.md_output_path)

        self.assertEqual(result_path, self.md_output_path)
        self.assertTrue(os.path.exists(self.md_output_path))

        with open(self.md_output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("# Stability Digest Report", content)

    def test_export_to_markdown_adapter_integration(self):
        random_key = f"key_{uuid.uuid4().hex[:6]}"
        random_val = random.random()

        self.anomaly_visualizer.digest = {random_key: random_val}

        result_path = self.exporter.export_to_markdown(self.md_output_path)

        self.assertEqual(result_path, self.md_output_path)
        self.assertTrue(os.path.exists(self.md_output_path))

        with open(self.md_output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("# Security Audit Digest Report", content)
        self.assertIn(random_key, content)


if __name__ == "__main__":
    unittest.main()