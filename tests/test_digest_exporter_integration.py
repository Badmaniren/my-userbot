import unittest
import json
import os
import uuid
import random
from unittest.mock import MagicMock
from skills.digest_exporter import DigestExporter, DigestExporterError
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.stability_digest import StabilityDigest

class TestDigestExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.output_json = f"test_report_{uuid.uuid4()}.json"
        self.output_html = f"test_report_{uuid.uuid4()}.html"
        self.stream_id = f"stream_{uuid.uuid4()}"

    def tearDown(self):
        for path in [self.output_json, self.output_html]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_export_json_and_html_with_real_skills(self):
        random_metric_val = random.randint(100, 999)

        detector = MagicMock()
        telemetry = MagicMock()
        stability = StabilityDigest(
            repo_path="/tmp",
            anomaly_detector=detector,
            system_telemetry=telemetry
        )
        visualizer = AnomalyVisualizer(digest={})
        exporter = DigestExporter(stability_digest=stability, anomaly_visualizer=visualizer)

        res_json = exporter.export_json_report(self.output_json)
        self.assertEqual(res_json, self.output_json)
        self.assertTrue(os.path.exists(self.output_json))

        with open(self.output_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertIsInstance(data, dict)
            self.assertIn("text_report", data)
            self.assertIn("ascii_graph", data)

        res_html = exporter.export_html_report(self.output_html)
        self.assertEqual(res_html, self.output_html)
        self.assertTrue(os.path.exists(self.output_html))

        with open(self.output_html, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("<html>", content)
            self.assertIn("Stability Digest Report", content)

    def test_export_stream_to_json_exception_handling(self):
        detector = MagicMock()
        telemetry = MagicMock()
        telemetry.collect_snapshot.side_effect = Exception("Stream failure")
        stability = StabilityDigest(
            repo_path="/tmp",
            anomaly_detector=detector,
            system_telemetry=telemetry
        )
        exporter = DigestExporter(stability_digest=stability)

        invalid_stream_id = f"nonexistent_{uuid.uuid4()}"
        with self.assertRaises(DigestExporterError):
            exporter.export_stream_to_json(invalid_stream_id, self.output_json)

    def test_adapters_json_and_html(self):
        detector = MagicMock()
        telemetry = MagicMock()
        stability = StabilityDigest(
            repo_path="/tmp",
            anomaly_detector=detector,
            system_telemetry=telemetry
        )
        visualizer = AnomalyVisualizer(digest={})
        exporter = DigestExporter(anomaly_visualizer=visualizer)

        res_json = exporter.export_to_json(self.output_json)
        self.assertEqual(res_json, self.output_json)
        self.assertTrue(os.path.exists(self.output_json))

        res_html = exporter.export_to_html(self.output_html)
        self.assertEqual(res_html, self.output_html)
        self.assertTrue(os.path.exists(self.output_html))

        with open(self.output_html, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("<html>", content)
            self.assertIn("<body>", content)

if __name__ == "__main__":
    unittest.main()