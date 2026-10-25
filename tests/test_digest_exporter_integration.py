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
        self.random_suffix = uuid.uuid4().hex[:8]
        self.json_output_path = f"test_report_{self.random_suffix}.json"
        self.html_output_path = f"test_report_{self.random_suffix}.html"
        
        self.metric_value = random.randint(100, 999)
        self.stream_id_val = f"stream_{uuid.uuid4().hex[:6]}"
        
        class MockStabilityDigest(StabilityDigest):
            def __init__(self, val):
                self.val = val
            def export_digest_stream(self, stream_id):
                return {"stream_id": stream_id, "data": self.val}

        class MockAnomalyVisualizer(AnomalyVisualizer):
            def __init__(self, val):
                self.val = val
                self.digest = {"random_digest_key": val}
            def get_summary_metrics(self):
                return {"metric_code": self.val}
            def render_text(self):
                return f"TEXT_REP_{self.val}"
            def render_ascii_correlation_graph(self):
                return f"ASCII_GRAPH_{self.val}"

        self.stability_digest = MockStabilityDigest(self.metric_value)
        self.anomaly_visualizer = MockAnomalyVisualizer(self.metric_value)
        
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
        result_path = self.exporter.export_json_report(self.json_output_path)
        self.assertEqual(result_path, self.json_output_path)
        self.assertTrue(os.path.exists(self.json_output_path))
        
        with open(self.json_output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.assertEqual(data.get("metric_code"), self.metric_value)
        self.assertEqual(data.get("text_report"), f"TEXT_REP_{self.metric_value}")
        self.assertEqual(data.get("ascii_graph"), f"ASCII_GRAPH_{self.metric_value}")

    def test_export_html_report_integration(self):
        result_path = self.exporter.export_html_report(self.html_output_path)
        self.assertEqual(result_path, self.html_output_path)
        self.assertTrue(os.path.exists(self.html_output_path))
        
        with open(self.html_output_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn("<html>", content)
        self.assertIn(str(self.metric_value), content)
        self.assertIn(f"TEXT_REP_{self.metric_value}", content)
        self.assertIn(f"ASCII_GRAPH_{self.metric_value}", content)

    def test_export_stream_to_json_integration(self):
        result_path = self.exporter.export_stream_to_json(self.stream_id_val, self.json_output_path)
        self.assertEqual(result_path, self.json_output_path)
        self.assertTrue(os.path.exists(self.json_output_path))
        
        with open(self.json_output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.assertEqual(data.get("stream_id"), self.stream_id_val)
        self.assertEqual(data.get("data"), self.metric_value)

    def test_export_to_json_adapter(self):
        result_path = self.exporter.export_to_json(self.json_output_path)
        self.assertEqual(result_path, self.json_output_path)
        self.assertTrue(os.path.exists(self.json_output_path))
        
        with open(self.json_output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.assertEqual(data.get("random_digest_key"), self.metric_value)

    def test_export_to_html_adapter(self):
        result_path = self.exporter.export_to_html(self.html_output_path)
        self.assertEqual(result_path, self.html_output_path)
        self.assertTrue(os.path.exists(self.html_output_path))
        
        with open(self.html_output_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn("<html><body><pre>", content)
        self.assertIn(str(self.metric_value), content)

    def test_exporter_exception_handling(self):
        broken_exporter = DigestExporter(stability_digest=None, anomaly_visualizer=None)
        with self.assertRaises(DigestExporterError):
            broken_exporter.export_json_report(self.json_output_path)

if __name__ == "__main__":
    unittest.main()