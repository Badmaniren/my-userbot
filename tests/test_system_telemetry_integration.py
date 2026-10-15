import unittest
import uuid
import random
import tempfile
import shutil
from pathlib import Path

from skills.system_telemetry import SystemTelemetry, SystemTelemetryError
from skills.anomaly_detector import AnomalyDetector
from skills.autonomous_engine import AutonomousEngine
from skills.git_inspector import GitInspector
from skills.hypothesis_generator import HypothesisGenerator
from skills.lesson_parser import LessonParser
from skills.patch_executor import PatchExecutor
from skills.patch_verifier import PatchVerifier

class TestSystemTelemetryIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.test_dir)
        
        # Инициализация реальных компонентов без моков
        self.git_inspector = GitInspector(str(self.repo_path))
        self.lesson_parser = LessonParser(self.git_inspector)
        self.hypothesis_generator = HypothesisGenerator(self.git_inspector, self.lesson_parser)
        self.patch_executor = PatchExecutor(str(self.repo_path), self.git_inspector, self.lesson_parser)
        self.patch_verifier = PatchVerifier(str(self.repo_path), self.git_inspector, self.patch_executor)
        
        threshold = random.uniform(1.0, 5.0)
        self.anomaly_detector = AnomalyDetector(
            repo_path=str(self.repo_path),
            threshold=threshold,
            git_inspector=self.git_inspector,
            patch_verifier=self.patch_verifier
        )
        
        self.autonomous_engine = AutonomousEngine(
            repo_path=str(self.repo_path),
            git_inspector=self.git_inspector,
            lesson_parser=self.lesson_parser,
            hypothesis_generator=self.hypothesis_generator,
            patch_executor=self.patch_executor,
            patch_verifier=self.patch_verifier
        )
        
        self.telemetry = SystemTelemetry(
            repo_path=str(self.repo_path),
            anomaly_detector=self.anomaly_detector,
            autonomous_engine=self.autonomous_engine
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_telemetry_and_autonomous_cycle_integration(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = random.uniform(10.0, 100.0)
        execution_id = uuid.uuid4().hex

        self.telemetry.record_metric(metric_name, metric_value)
        history = self.telemetry.get_metric_history(metric_name)
        
        self.assertIn(metric_value, history)

        patch_data = {
            "id": execution_id,
            "content": f"# Test change {uuid.uuid4().hex}"
        }

        analysis_result = self.telemetry.analyze_execution_telemetry(execution_id, {metric_name: metric_value})
        self.assertIsInstance(analysis_result, dict)

        is_anomaly = self.telemetry.detect_anomaly(metric_name, metric_value * random.uniform(1.5, 3.0))
        self.assertIsInstance(is_anomaly, bool)

        telemetry_summary = self.telemetry.get_telemetry_summary()
        self.assertIsInstance(telemetry_summary, dict)

if __name__ == "__main__":
    unittest.main()