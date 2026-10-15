import unittest
import tempfile
import shutil
import uuid
import random
import os

from skills.system_telemetry import SystemTelemetry
from skills.anomaly_detector import AnomalyDetector
from skills.git_inspector import GitInspector
from skills.patch_verifier import PatchVerifier
from skills.patch_executor import PatchExecutor
from skills.lesson_parser import LessonParser

class TestSystemTelemetryIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.baseline_value = float(random.randint(10, 50))
        self.anomaly_value = float(random.randint(500, 1000))

        self.git_inspector = GitInspector(self.test_dir)
        self.lesson_parser = LessonParser(self.git_inspector)
        self.patch_executor = PatchExecutor(self.test_dir, self.git_inspector, self.lesson_parser)
        self.patch_verifier = PatchVerifier(self.test_dir, self.git_inspector, self.patch_executor)

        self.anomaly_detector = AnomalyDetector(
            repo_path=self.test_dir,
            threshold=2.0,
            git_inspector=self.git_inspector,
            patch_verifier=self.patch_verifier
        )

        self.system_telemetry = SystemTelemetry(
            repo_path=self.test_dir,
            anomaly_detector=self.anomaly_detector
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_system_telemetry_integration_with_anomaly_detector(self):
        self.system_telemetry.record_metric(self.metric_name, self.baseline_value)
        self.system_telemetry.record_metric(self.metric_name, self.baseline_value + float(random.randint(1, 5)))

        history = self.system_telemetry.get_metric_history(self.metric_name)
        self.assertIsInstance(history, list)
        self.assertGreaterEqual(len(history), 2)

        is_anomaly = self.system_telemetry.detect_anomaly(self.metric_name, self.anomaly_value)
        self.assertTrue(is_anomaly)

        execution_id = uuid.uuid4().hex
        metrics_payload = {
            self.metric_name: self.anomaly_value,
            f"cpu_load_{uuid.uuid4().hex[:4]}": float(random.randint(80, 100))
        }

        analysis_result = self.system_telemetry.analyze_execution_metrics(execution_id, metrics_payload)
        self.assertIsInstance(analysis_result, dict)

        telemetry_status = self.system_telemetry.get_telemetry_summary()
        self.assertIsInstance(telemetry_status, dict)

if __name__ == "__main__":
    unittest.main()