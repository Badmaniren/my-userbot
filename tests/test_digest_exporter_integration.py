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
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.json_output = os.path.join(self.test_dir, f"test_report_{uuid.uuid4()}.json")
        self.html_output = os.path.join(self.test_dir, f"test_report_{uuid.uuid4()}.html")
        self.stream_json_output = os.path.join(self.test_dir, f"test_stream_{uuid.uuid4()}.json")

        self.random_metric_val = random.randint(100, 999)
        self.mock_digest_data = {
            "summary": "Integration test digest",
            "metric": self.random_metric_val,
            "status": "stable"
        }

        self.visualizer = AnomalyVisualizer(digest=self.mock_digest_data)
        self.digest_module = StabilityDigest(repo_path=self.test_dir, anomaly_detector=None, system_telemetry=None)
        
        self.exporter = DigestExporter(
            stability_digest=self.digest_module,
            anomaly_visualizer=self.visualizer
        )

    def tearDown(self):
        for path in [self.json_output, self.html_output, self.stream_json_output]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_export_json_report_integration(self):
        result_path = self.exporter.export_json_report(self.json_output)
        
        self.assertEqual(result_path, self.json_output)
        self.assertTrue(os.path.exists(self.json_output))

        with open(self.json_output, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn('text_report', data)
        self.assertIn('ascii_graph', data)

    def test_export_html_report_integration(self):
        result_path = self.exporter.export_html_report(self.html_output)
        
        self.assertEqual(result_path, self.html_output)
        self.assertTrue(os.path.exists(self.html_output))

        with open(self.html_output, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn("Stability Digest Report", content)

    def test_export_to_json_adapter_integration(self):
        result_path = self.exporter.export_to_json(self.json_output)
        
        self.assertEqual(result_path, self.json_output)
        self.assertTrue(os.path.exists(self.json_output))

        with open(self.json_output, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(data.get("metric"), self.random_metric_val)

    def test_export_to_html_adapter_integration(self):
        result_path = self.exporter.export_to_html(self.html_output)
        
        self.assertEqual(result_path, self.html_output)
        self.assertTrue(os.path.exists(self.html_output))

        with open(self.html_output, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn(str(self.random_metric_val), content)

if __name__ == '__main__':
    unittest.main()