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
        self.output_json = f"test_report_{uuid.uuid4()}.json"
        self.output_html = f"test_report_{uuid.uuid4()}.html"
        self.stream_id = str(uuid.uuid4())
        self.random_metric_value = random.randint(100, 999)

    def tearDown(self):
        for path in [self.output_json, self.output_html]:
            if os.path.exists(path):
                os.remove(path)

    def test_export_json_report_integration(self):
        digest = StabilityDigest()
        visualizer = AnomalyVisualizer(stability_digest=digest)
        exporter = DigestExporter(stability_digest=digest, anomaly_visualizer=visualizer)

        result_path = exporter.export_json_report(self.output_json)
        self.assertEqual(result_path, self.output_json)
        self.assertTrue(os.path.exists(self.output_json))

        with open(self.output_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertIn('text_report', data)
            self.assertIn('ascii_graph', data)

    def test_export_html_report_integration(self):
        digest = StabilityDigest()
        visualizer = AnomalyVisualizer(stability_digest=digest)
        exporter = DigestExporter(stability_digest=digest, anomaly_visualizer=visualizer)

        result_path = exporter.export_html_report(self.output_html)
        self.assertEqual(result_path, self.output_html)
        self.assertTrue(os.path.exists(self.output_html))

        with open(self.output_html, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("<html>", content)
            self.assertIn("Stability Digest Report", content)

    def test_export_stream_to_json_integration(self):
        digest = StabilityDigest()
        exporter = DigestExporter(stability_digest=digest)

        result_path = exporter.export_stream_to_json(self.stream_id, self.output_json)
        self.assertEqual(result_path, self.output_json)
        self.assertTrue(os.path.exists(self.output_json))

        with open(self.output_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertIsInstance(data, (dict, list))

    def test_export_to_json_adapter_integration(self):
        digest = StabilityDigest()
        digest.digest = {"random_key": self.random_metric_value}
        exporter = DigestExporter(stability_digest=digest)

        result_path = exporter.export_to_json(self.output_json)
        self.assertEqual(result_path, self.output_json)
        self.assertTrue(os.path.exists(self.output_json))

        with open(self.output_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data.get("random_key"), self.random_metric_value)

    def test_export_to_html_adapter_integration(self):
        digest = StabilityDigest()
        digest.digest = {"random_key": self.random_metric_value}
        exporter = DigestExporter(stability_digest=digest)

        result_path = exporter.export_to_html(self.output_html)
        self.assertEqual(result_path, self.output_html)
        self.assertTrue(os.path.exists(self.output_html))

        with open(self.output_html, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(str(self.random_metric_value), content)

    def test_exporter_none_type_handling_exception(self):
        exporter = DigestExporter(stability_digest=None, anomaly_visualizer=None)
        with self.assertRaises(DigestExporterError):
            exporter.export_json_report(self.output_json)

        with self.assertRaises(DigestExporterError):
            exporter.export_html_report(self.output_html)

        with self.assertRaises(DigestExporterError):
            exporter.export_stream_to_json(self.stream_id, self.output_json)

if __name__ == '__main__':
    unittest.main()