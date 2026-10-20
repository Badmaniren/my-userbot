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

        self.json_output_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.json")
        self.html_output_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.html")
        self.stream_json_path = os.path.join(self.test_dir, f"stream_{uuid.uuid4().hex}.json")

        self.stability_digest = StabilityDigest()
        self.anomaly_visualizer = AnomalyVisualizer()

        self.exporter = DigestExporter(
            stability_digest=self.stability_digest,
            anomaly_visualizer=self.anomaly_visualizer
        )

        self.random_stream_id = f"stream_{uuid.uuid4().hex[:8]}"

    def tearDown(self):
        for path in [self.json_output_path, self.html_output_path, self.stream_json_path]:
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
        result_path = self.exporter.export_json_report(self.json_output_path)
        self.assertEqual(result_path, self.json_output_path)
        self.assertTrue(os.path.exists(self.json_output_path))

        with open(self.json_output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIsInstance(data, dict)
        self.assertIn('text_report', data)
        self.assertIn('ascii_graph', data)

    def test_export_html_report_integration(self):
        result_path = self.exporter.export_html_report(self.html_output_path)
        self.assertEqual(result_path, self.html_output_path)
        self.assertTrue(os.path.exists(self.html_output_path))

        with open(self.html_output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn("Stability Digest Report", content)

    def test_export_stream_to_json_integration(self):
        try:
            result_path = self.exporter.export_stream_to_json(self.random_stream_id, self.stream_json_path)
            self.assertEqual(result_path, self.stream_json_path)
            self.assertTrue(os.path.exists(self.stream_json_path))
        except DigestExporterError:
            pass

    def test_export_to_json_adapter_integration(self):
        result_path = self.exporter.export_to_json(self.json_output_path)
        self.assertEqual(result_path, self.json_output_path)
        self.assertTrue(os.path.exists(self.json_output_path))

        with open(self.json_output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)

    def test_export_to_html_adapter_integration(self):
        result_path = self.exporter.export_to_html(self.html_output_path)
        self.assertEqual(result_path, self.html_output_path)
        self.assertTrue(os.path.exists(self.html_output_path))

        with open(self.html_output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("<html>", content)

if __name__ == '__main__':
    unittest.main()