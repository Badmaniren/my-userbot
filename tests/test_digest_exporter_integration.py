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
        self.output_json = f"test_report_{uuid.uuid4()}.json"
        self.output_html = f"test_report_{uuid.uuid4()}.html"
        self.stream_id = str(uuid.uuid4())
        
        self.random_metric_val = random.randint(100, 999)
        self.random_text_msg = f"audit_msg_{uuid.uuid4()}"

        class MockVisualizer:
            def __init__(self, val, msg):
                self.val = val
                self.msg = msg
                self.digest = {"random_key": str(uuid.uuid4()), "value": val}

            def get_summary_metrics(self):
                return {"metric_code": self.val}

            def render_text(self):
                return f"Text report data: {self.msg}"

            def render_ascii_correlation_graph(self):
                return "[*]--[*]"

        class MockStabilityDigest:
            def __init__(self, sid, val):
                self.sid = sid
                self.val = val

            def export_digest_stream(self, stream_id):
                return {"stream_id": stream_id, "data": self.val}

        self.visualizer = MockVisualizer(self.random_metric_val, self.random_text_msg)
        self.stability_digest = MockStabilityDigest(self.stream_id, self.random_metric_val)
        
        self.exporter = DigestExporter(
            stability_digest=self.stability_digest,
            anomaly_visualizer=self.visualizer
        )

    def tearDown(self):
        for path in [self.output_json, self.output_html]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_export_json_report_integration(self):
        result_path = self.exporter.export_json_report(self.output_json)
        self.assertEqual(result_path, self.output_json)
        self.assertTrue(os.path.exists(self.output_json))

        with open(self.output_json, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn('metric_code', data)
        self.assertEqual(data['metric_code'], self.random_metric_val)
        self.assertIn('text_report', data)
        self.assertIn(self.random_text_msg, data['text_report'])
        self.assertIn('ascii_graph', data)

    def test_export_html_report_integration(self):
        result_path = self.exporter.export_html_report(self.output_html)
        self.assertEqual(result_path, self.output_html)
        self.assertTrue(os.path.exists(self.output_html))

        with open(self.output_html, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn(str(self.random_metric_val), content)
        self.assertIn(self.random_text_msg, content)

    def test_export_stream_to_json_integration(self):
        result_path = self.exporter.export_stream_to_json(self.stream_id, self.output_json)
        self.assertEqual(result_path, self.output_json)
        self.assertTrue(os.path.exists(self.output_json))

        with open(self.output_json, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(data.get("stream_id"), self.stream_id)
        self.assertEqual(data.get("data"), self.random_metric_val)

    def test_export_to_json_adapter(self):
        result_path = self.exporter.export_to_json(self.output_json)
        self.assertEqual(result_path, self.output_json)
        self.assertTrue(os.path.exists(self.output_json))

        with open(self.output_json, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(data.get("value"), self.random_metric_val)

    def test_export_to_html_adapter(self):
        result_path = self.exporter.export_to_html(self.output_html)
        self.assertEqual(result_path, self.output_html)
        self.assertTrue(os.path.exists(self.output_html))

        with open(self.output_html, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn(str(self.random_metric_val), content)

if __name__ == '__main__':
    unittest.main()