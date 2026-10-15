import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.stability_digest import StabilityDigest
from skills.system_telemetry import SystemTelemetry
from skills.anomaly_detector import AnomalyDetector
from skills.git_inspector import GitInspector
from skills.patch_verifier import PatchVerifier
from skills.patch_executor import PatchExecutor
from skills.lesson_parser import LessonParser
from skills.autonomous_engine import AutonomousEngine
from skills.hypothesis_generator import HypothesisGenerator


class TestStabilityDigestIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Initialize real components without mocks
        self.git_inspector = GitInspector(self.repo_path)
        self.lesson_parser = LessonParser(self.git_inspector)
        self.hypothesis_generator = HypothesisGenerator(self.git_inspector, self.lesson_parser)
        self.patch_executor = PatchExecutor(self.repo_path, self.git_inspector, self.lesson_parser)
        self.patch_verifier = PatchVerifier(self.repo_path, self.git_inspector, self.patch_executor)
        
        threshold = random.uniform(1.0, 10.0)
        self.anomaly_detector = AnomalyDetector(
            repo_path=self.repo_path,
            threshold=threshold,
            git_inspector=self.git_inspector,
            patch_verifier=self.patch_verifier
        )
        
        self.autonomous_engine = AutonomousEngine(
            repo_path=self.repo_path,
            git_inspector=self.git_inspector,
            lesson_parser=self.lesson_parser,
            hypothesis_generator=self.hypothesis_generator,
            patch_executor=self.patch_executor,
            patch_verifier=self.patch_verifier
        )
        
        self.system_telemetry = SystemTelemetry(
            repo_path=self.repo_path,
            anomaly_detector=self.anomaly_detector,
            autonomous_engine=self.autonomous_engine
        )
        
        self.stability_digest = StabilityDigest(
            repo_path=self.repo_path,
            system_telemetry=self.system_telemetry,
            anomaly_detector=self.anomaly_detector
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_stability_digest_integration_flow(self):
        execution_id = str(uuid.uuid4())
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = random.uniform(50.0, 500.0)

        self.system_telemetry.record_metric(metric_name, metric_value)
        snapshot = self.system_telemetry.collect_snapshot(execution_id)
        
        self.assertIsInstance(snapshot, dict)

        anomalies = self.anomaly_detector.detect_anomalies()
        self.assertIsInstance(anomalies, dict)

        digest = self.stability_digest.generate_digest(execution_id)
        
        self.assertIsInstance(digest, dict)
        self.assertTrue(len(digest) > 0)
        
        summary = self.system_telemetry.get_telemetry_summary()
        self.assertIsInstance(summary, dict)


if __name__ == '__main__':
    unittest.main()