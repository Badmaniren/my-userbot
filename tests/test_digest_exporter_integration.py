import unittest
import os
import json
import uuid
import random
from skills.digest_exporter import DigestExporter, DigestExporterError
from skills.stability_digest import StabilityDigest
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.anomaly_correlator import AnomalyCorrelator
from skills.system_telemetry import SystemTelemetry


class TestDigestExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = f"test_dir_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)

        self.repo_path = self.test_dir
        self.log_path = os.path.join(self.test_dir, "anomalies.log")
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
        for filename in os.listdir(self.test_dir):
            file_path = os.path.join(self.test_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_export_json_report_integration(self):
        filename = f"report_{uuid.uuid4().hex}.json"
        output_path = os.path.join(self.test_dir, filename)

        result_path = self.exporter.export_json_report(output_path)

        self.assertEqual(result_path, output_path)
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn('text_report', data)
        self.assertIn('ascii_graph', data)

    def test_export_html_report_integration(self):
        filename = f"report_{uuid.uuid4().hex}.html"
        output_path = os.path.join(self.test_dir, filename)

        result_path = self.exporter.export_html_report(output_path)

        self.assertEqual(result_path, output_path)
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn("</html>", content)
        self.assertIn("Stability Digest Report", content)

    def test_export_to_json_adapter_integration(self):
        filename = f"adapter_{uuid.uuid4().hex}.json"
        output_path = os.path.join(self.test_dir, filename)

        random_metric_val = random.randint(100, 999)
        self.anomaly_visualizer.digest = {"random_security_metric": random_metric_val}

        result_path = self.exporter.export_to_json(output_path)

        self.assertEqual(result_path, output_path)
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(data.get("random_security_metric"), random_metric_val)

    def test_export_to_html_adapter_integration(self):
        filename = f"adapter_{uuid.uuid4().hex}.html"
        output_path = os.path.join(self.test_dir, filename)

        unique_marker = f"marker_{uuid.uuid4().hex}"
        self.anomaly_visualizer.digest = {"marker": unique_marker}

        result_path = self.exporter.export_to_html(output_path)

        self.assertEqual(result_path, output_path)
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn(unique_marker, content)
        self.assertIn("<html>", content)


if __name__ == '__main__':
    unittest.main()