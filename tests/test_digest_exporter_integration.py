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
        self.test_dir = f"test_dir_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)

        self.json_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.json")
        self.html_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.html")

        self.stability_digest = StabilityDigest()
        self.anomaly_visualizer = AnomalyVisualizer()

        self.exporter = DigestExporter(
            stability_digest=self.stability_digest,
            anomaly_visualizer=self.anomaly_visualizer
        )

    def tearDown(self):
        for path in [self.json_path, self.html_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_export_json_report_integration(self):
        random_value = random.randint(100, 999)
        self.anomaly_visualizer.digest = {"metric_test": random_value}

        result_path = self.exporter.export_json_report(self.json_path)

        self.assertEqual(result_path, self.json_path)
        self.assertTrue(os.path.exists(self.json_path))

        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn('text_report', data)
        self.assertIn('ascii_graph', data)

    def test_export_html_report_integration(self):
        random_str = uuid.uuid4().hex
        self.anomaly_visualizer.digest = {"unique_id": random_str}

        result_path = self.exporter.export_html_report(self.html_path)

        self.assertEqual(result_path, self.html_path)
        self.assertTrue(os.path.exists(self.html_path))

        with open(self.html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn("</html>", content)

    def test_export_to_json_adapter_integration(self):
        random_key = uuid.uuid4().hex
        random_val = random.random()
        self.anomaly_visualizer.digest = {random_key: random_val}

        result_path = self.exporter.export_to_json(self.json_path)

        self.assertEqual(result_path, self.json_path)
        self.assertTrue(os.path.exists(self.json_path))

        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn(random_key, data)
        self.assertEqual(data[random_key], random_val)


if __name__ == '__main__':
    unittest.main()