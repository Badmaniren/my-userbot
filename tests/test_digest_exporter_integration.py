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
        self.json_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.json")
        self.html_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.html")

    def tearDown(self):
        for path in [self.json_path, self.html_path]:
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_export_pipeline_integration(self):
        random_metric_val = random.randint(100, 999)
        random_key = f"key_{uuid.uuid4().hex[:6]}"

        digest_data = {
            random_key: random_metric_val,
            "status": "stable",
            "score": random.random()
        }

        stability_digest = StabilityDigest()
        stability_digest.digest = digest_data

        anomaly_visualizer = AnomalyVisualizer(stability_digest=stability_digest)

        exporter = DigestExporter(
            stability_digest=stability_digest,
            anomaly_visualizer=anomaly_visualizer
        )

        exported_json = exporter.export_to_json(self.json_path)
        self.assertEqual(exported_json, self.json_path)
        self.assertTrue(os.path.exists(self.json_path))

        with open(self.json_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        self.assertIn(random_key, loaded_data)
        self.assertEqual(loaded_data[random_key], random_metric_val)
        self.assertEqual(loaded_data["status"], "stable")

        exported_html = exporter.export_to_html(self.html_path)
        self.assertEqual(exported_html, self.html_path)
        self.assertTrue(os.path.exists(self.html_path))

        with open(self.html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        self.assertIn("<html>", html_content)
        self.assertIn(str(random_metric_val), html_content)

    def test_export_json_report_with_metrics(self):
        rand_val = random.randint(1000, 9999)
        stability_digest = StabilityDigest()
        stability_digest.digest = {"metric_test": rand_val}

        anomaly_visualizer = AnomalyVisualizer(stability_digest=stability_digest)

        exporter = DigestExporter(
            stability_digest=stability_digest,
            anomaly_visualizer=anomaly_visualizer
        )

        result_path = exporter.export_json_report(self.json_path)
        self.assertEqual(result_path, self.json_path)
        self.assertTrue(os.path.exists(self.json_path))

        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("text_report", data)
        self.assertIn("ascii_graph", data)


if __name__ == "__main__":
    unittest.main()