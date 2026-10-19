import unittest
import os
import json
import uuid
import random
from skills.digest_exporter import DigestExporter, DigestExporterError
from skills.stability_digest import StabilityDigest
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.system_telemetry import SystemTelemetry
from skills.anomaly_correlator import AnomalyCorrelator


class TestDigestExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = f"test_dir_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.json_output_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.json")
        self.html_output_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.html")
        self.log_path = os.path.join(self.test_dir, "anomalies.log")

        self.anomaly_detector = AnomalyCorrelator(
            repo_path=self.test_dir,
            log_path=self.log_path,
            threshold=0.5,
            detector=None,
            logger=None
        )
        self.system_telemetry = SystemTelemetry(
            repo_path=self.test_dir,
            anomaly_detector=self.anomaly_detector,
            autonomous_engine=None
        )
        self.stability_digest = StabilityDigest(
            repo_path=self.test_dir,
            anomaly_detector=self.anomaly_detector,
            system_telemetry=self.system_telemetry
        )
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
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_export_json_report_integration(self):
        random_val = random.randint(100, 999)
        if hasattr(self.anomaly_visualizer, 'digest') and isinstance(self.anomaly_visualizer.digest, dict):
            self.anomaly_visualizer.digest['integration_metric'] = random_val

        result_path = self.exporter.export_json_report(self.json_output_path)

        self.assertEqual(result_path, self.json_output_path)
        self.assertTrue(os.path.exists(self.json_output_path))

        with open(self.json_output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIsInstance(data, dict)
        self.assertIn('text_report', data)
        self.assertIn('ascii_graph', data)

    def test_export_html_report_integration(self):
        result_path = self.exporter.export_html_report(self.html_output_path)

        self.assertEqual(result_path, self.html_output_path)
        self.assertTrue(os.path.exists(self.html_output_path))

        with open(self.html_output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn("Stability Digest Report", content)

    def test_export_to_json_integration(self):
        random_key = f"key_{uuid.uuid4().hex[:6]}"
        random_val = random.randint(1000, 9999)

        self.anomaly_visualizer.digest = {random_key: random_val}

        result_path = self.exporter.export_to_json(self.json_output_path)

        self.assertEqual(result_path, self.json_output_path)
        self.assertTrue(os.path.exists(self.json_output_path))

        with open(self.json_output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn(random_key, data)
        self.assertEqual(data[random_key], random_val)

    def test_export_to_html_integration(self):
        random_key = f"key_{uuid.uuid4().hex[:6]}"
        random_val = random.randint(1000, 9999)

        self.anomaly_visualizer.digest = {random_key: random_val}

        result_path = self.exporter.export_to_html(self.html_output_path)

        self.assertEqual(result_path, self.html_output_path)
        self.assertTrue(os.path.exists(self.html_output_path))

        with open(self.html_output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn(random_key, content)
        self.assertIn(str(random_val), content)

    def test_export_error_handling_raises_custom(self):
        invalid_path = os.path.join(self.test_dir, "non_existent_subdir", f"invalid_{uuid.uuid4().hex}.json")

        with self.assertRaises(DigestExporterError):
            self.exporter.export_json_report(invalid_path)


if __name__ == '__main__':
    unittest.main()