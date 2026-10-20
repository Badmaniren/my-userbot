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
        self.rand_str = str(uuid.uuid4())
        self.json_output_path = f"test_report_{self.rand_str}.json"
        self.html_output_path = f"test_report_{self.rand_str}.html"

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

    def test_integration_export_json_report(self):
        result_path = self.exporter.export_json_report(self.json_output_path)

        self.assertEqual(result_path, self.json_output_path)
        self.assertTrue(os.path.exists(self.json_output_path))

        with open(self.json_output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIsInstance(data, dict)
        self.assertIn('text_report', data)
        self.assertIn('ascii_graph', data)

    def test_integration_export_html_report(self):
        result_path = self.exporter.export_html_report(self.html_output_path)

        self.assertEqual(result_path, self.html_output_path)
        self.assertTrue(os.path.exists(self.html_output_path))

        with open(self.html_output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn("Stability Digest Report", content)

    def test_integration_adapters(self):
        json_adapter_path = f"adapter_{self.rand_str}.json"
        html_adapter_path = f"adapter_{self.rand_str}.html"

        try:
            res_json = self.exporter.export_to_json(json_adapter_path)
            self.assertEqual(res_json, json_adapter_path)
            self.assertTrue(os.path.exists(json_adapter_path))

            res_html = self.exporter.export_to_html(html_adapter_path)
            self.assertEqual(res_html, html_adapter_path)
            self.assertTrue(os.path.exists(html_adapter_path))
        finally:
            for path in [json_adapter_path, html_adapter_path]:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass


if __name__ == '__main__':
    unittest.main()