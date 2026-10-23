import unittest
import os
import json
import uuid
import random
import tempfile
import shutil
from skills.digest_exporter import DigestExporter, DigestExporterError
from skills.stability_digest import StabilityDigest
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.system_telemetry import SystemTelemetry
from skills.anomaly_correlator import AnomalyCorrelator


class TestDigestExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.log_path = os.path.join(self.test_dir, "anomalies.log")
        
        self.output_json = os.path.join(self.test_dir, f"test_report_{uuid.uuid4()}.json")
        self.output_html = os.path.join(self.test_dir, f"test_report_{uuid.uuid4()}.html")
        self.stream_id = f"stream_{random.randint(1000, 9999)}"

        self.anomaly_detector = AnomalyCorrelator(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=0.5,
            detector=None,
            logger=None
        )
        self.system_telemetry = SystemTelemetry(
            repo_path=self.repo_path,
            anomaly_detector=self.anomaly_detector,
            autonomous_engine=None
        )
        self.stability_digest = StabilityDigest(
            repo_path=self.repo_path,
            anomaly_detector=self.anomaly_detector,
            system_telemetry=self.system_telemetry
        )
        self.anomaly_visualizer = AnomalyVisualizer()
        
        self.exporter = DigestExporter(
            stability_digest=self.stability_digest,
            anomaly_visualizer=self.anomaly_visualizer
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_export_json_report_integration(self):
        result_path = self.exporter.export_json_report(self.output_json)

        self.assertEqual(result_path, self.output_json)
        self.assertTrue(os.path.exists(self.output_json))

        with open(self.output_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("text_report", data)
        self.assertIn("ascii_graph", data)

    def test_export_html_report_integration(self):
        result_path = self.exporter.export_html_report(self.output_html)

        self.assertEqual(result_path, self.output_html)
        self.assertTrue(os.path.exists(self.output_html))

        with open(self.output_html, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn("Stability Digest Report", content)

    def test_export_stream_to_json_integration(self):
        try:
            result_path = self.exporter.export_stream_to_json(self.stream_id, self.output_json)
            self.assertEqual(result_path, self.output_json)
            self.assertTrue(os.path.exists(self.output_json))
        except Exception as e:
            self.assertIsInstance(e, DigestExporterError)

    def test_export_adapters_integration(self):
        json_path = self.exporter.export_to_json(self.output_json)
        self.assertEqual(json_path, self.output_json)
        self.assertTrue(os.path.exists(self.output_json))

        html_path = self.exporter.export_to_html(self.output_html)
        self.assertEqual(html_path, self.output_html)
        self.assertTrue(os.path.exists(self.output_html))


if __name__ == "__main__":
    unittest.main()