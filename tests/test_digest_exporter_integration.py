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

    def test_digest_exporter_real_integration(self):
        rand_metric_val = random.randint(100, 999)
        rand_stream_id = f"stream_{uuid.uuid4().hex[:8]}"

        class DummyVisualizer:
            def __init__(self, val):
                self.val = val
                self.digest = {"metric_key": val, "random_tag": uuid.uuid4().hex}

            def get_summary_metrics(self):
                return {"summary_value": self.val}

            def render_text(self):
                return f"Text report metric: {self.val}"

            def render_ascii_correlation_graph(self):
                return f"[*--- {self.val} ---*]"

        class DummyDigest:
            def export_digest_stream(self, stream_id):
                return {"stream_id": stream_id, "status": "active", "payload_id": random.randint(1, 100)}

        visualizer = DummyVisualizer(rand_metric_val)
        digest = DummyDigest()

        exporter = DigestExporter(stability_digest=digest, anomaly_visualizer=visualizer)

        # Тест export_json_report
        res_json_path = exporter.export_json_report(self.json_path)
        self.assertTrue(os.path.exists(res_json_path))
        with open(res_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data.get("summary_value"), rand_metric_val)
            self.assertIn("Text report metric", data.get("text_report", ""))

        # Тест export_html_report
        res_html_path = exporter.export_html_report(self.html_path)
        self.assertTrue(os.path.exists(res_html_path))
        with open(res_html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            self.assertIn("<html>", html_content)
            self.assertIn(str(rand_metric_val), html_content)

        # Тест export_stream_to_json
        stream_json_path = os.path.join(self.test_dir, f"stream_{uuid.uuid4().hex}.json")
        try:
            res_stream_path = exporter.export_stream_to_json(rand_stream_id, stream_json_path)
            self.assertTrue(os.path.exists(res_stream_path))
            with open(res_stream_path, "r", encoding="utf-8") as f:
                stream_data = json.load(f)
                self.assertEqual(stream_data.get("stream_id"), rand_stream_id)
        finally:
            if os.path.exists(stream_json_path):
                os.remove(stream_json_path)

        # Тест адаптеров export_to_json / export_to_html
        adapter_json_path = os.path.join(self.test_dir, f"adapter_{uuid.uuid4().hex}.json")
        try:
            res_adapter_path = exporter.export_to_json(adapter_json_path)
            self.assertTrue(os.path.exists(res_adapter_path))
            with open(res_adapter_path, "r", encoding="utf-8") as f:
                adapter_data = json.load(f)
                self.assertEqual(adapter_data.get("metric_key"), rand_metric_val)
        finally:
            if os.path.exists(adapter_json_path):
                os.remove(adapter_json_path)


if __name__ == "__main__":
    unittest.main()