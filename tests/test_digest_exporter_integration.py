import unittest
import os
import uuid
import random
from unittest.mock import MagicMock
from skills.digest_exporter import DigestExporter, DigestExporterError
from skills.stability_digest import StabilityDigest
from skills.anomaly_visualizer import AnomalyVisualizer


class TestDigestExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = f"test_export_dir_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.json_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.json")
        self.html_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.html")

    def tearDown(self):
        for path in [self.json_path, self.html_path]:
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_digest_exporter_with_real_dependencies(self):
        rand_metric_val = random.randint(100, 999)
        rand_stream_id = f"stream_{uuid.uuid4().hex[:8]}"

        stability_digest = StabilityDigest(
            repo_path=".",
            anomaly_detector=MagicMock(),
            system_telemetry=MagicMock()
        )
        stability_digest.digest = {"random_key": rand_metric_val, "stream_id": rand_stream_id}

        anomaly_visualizer = AnomalyVisualizer()
        anomaly_visualizer.digest = {"random_key": rand_metric_val, "visualizer_id": uuid.uuid4().hex, "metrics": {"random_key": rand_metric_val}}

        exporter = DigestExporter(stability_digest=stability_digest, anomaly_visualizer=anomaly_visualizer)

        res_json = exporter.export_json_report(self.json_path)
        self.assertEqual(res_json, self.json_path)
        self.assertTrue(os.path.exists(self.json_path))

        with open(self.json_path, 'r', encoding='utf-8') as f:
            content_json = f.read()
            self.assertIn(str(rand_metric_val), content_json)

        res_html = exporter.export_html_report(self.html_path)
        self.assertEqual(res_html, self.html_path)
        self.assertTrue(os.path.exists(self.html_path))

        with open(self.html_path, 'r', encoding='utf-8') as f:
            content_html = f.read()
            self.assertIn("Digest Report", content_html)

        adapter_json_path = os.path.join(self.test_dir, f"adapter_{uuid.uuid4().hex}.json")
        try:
            res_adapter = exporter.export_to_json(adapter_json_path)
            self.assertEqual(res_adapter, adapter_json_path)
            self.assertTrue(os.path.exists(adapter_json_path))
        finally:
            if os.path.exists(adapter_json_path):
                os.remove(adapter_json_path)

    def test_digest_exporter_none_safety(self):
        exporter = DigestExporter(stability_digest=None, anomaly_visualizer=None)

        res_json = exporter.export_json_report(self.json_path)
        self.assertTrue(os.path.exists(res_json))

        res_html = exporter.export_html_report(self.html_path)
        self.assertTrue(os.path.exists(res_html))

        stream_json_path = os.path.join(self.test_dir, f"stream_{uuid.uuid4().hex}.json")
        try:
            res_stream = exporter.export_stream_to_json(uuid.uuid4().hex, stream_json_path)
            self.assertTrue(os.path.exists(res_stream))
        finally:
            if os.path.exists(stream_json_path):
                os.remove(stream_json_path)


if __name__ == '__main__':
    unittest.main()