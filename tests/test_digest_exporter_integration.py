import unittest
import json
import os
import uuid
import random
from skills.digest_exporter import DigestExporter, DigestExporterError
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.stability_digest import StabilityDigest

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

    def test_export_json_and_html_integration(self):
        random_metric_val = random.randint(100, 999)
        random_text_msg = f"anomaly_msg_{uuid.uuid4().hex}"

        class DummyVisualizer:
            def __init__(self, val, msg):
                self.val = val
                self.msg = msg
                self.digest = {"random_key": uuid.uuid4().hex}

            def get_summary_metrics(self):
                return {"metric": self.val}

            def render_text(self):
                return self.msg

            def render_ascii_correlation_graph(self):
                return " *---* "

        visualizer = DummyVisualizer(random_metric_val, random_text_msg)
        exporter = DigestExporter(stability_digest=None, anomaly_visualizer=visualizer)

        res_json = exporter.export_json_report(self.json_path)
        self.assertEqual(res_json, self.json_path)
        self.assertTrue(os.path.exists(self.json_path))

        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data.get("metric"), random_metric_val)
            self.assertEqual(data.get("text_report"), random_text_msg)
            self.assertEqual(data.get("ascii_graph"), " *---* ")

        res_html = exporter.export_html_report(self.html_path)
        self.assertEqual(res_html, self.html_path)
        self.assertTrue(os.path.exists(self.html_path))

        with open(self.html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(str(random_metric_val), content)
            self.assertIn(random_text_msg, content)

    def test_export_to_json_and_html_adapters(self):
        random_digest_val = uuid.uuid4().hex

        class DummyVisualizerAdapter:
            def __init__(self, val):
                self.digest = {"adapter_id": val}

        visualizer = DummyVisualizerAdapter(random_digest_val)
        exporter = DigestExporter(stability_digest=None, anomaly_visualizer=visualizer)

        res_json = exporter.export_to_json(self.json_path)
        self.assertEqual(res_json, self.json_path)
        self.assertTrue(os.path.exists(self.json_path))

        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data.get("adapter_id"), random_digest_val)

        res_html = exporter.export_to_html(self.html_path)
        self.assertEqual(res_html, self.html_path)
        self.assertTrue(os.path.exists(self.html_path))

        with open(self.html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(random_digest_val, content)

    def test_exporter_error_handling(self):
        class FaultyVisualizer:
            def get_summary_metrics(self):
                raise RuntimeError("Visualizer critical failure")

        exporter = DigestExporter(stability_digest=None, anomaly_visualizer=FaultyVisualizer())

        with self.assertRaises(DigestExporterError):
            exporter.export_json_report(self.json_path)

        with self.assertRaises(DigestExporterError):
            exporter.export_html_report(self.html_path)

if __name__ == '__main__':
    unittest.main()