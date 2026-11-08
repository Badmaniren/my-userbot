import unittest
import uuid
import random
import os
import tempfile
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_logger import RepoLogger

class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_id = str(uuid.uuid4())
        self.logger = RepoLogger()
        self.pulse_engine = RepoHealthPulseEngine()
        self.anomaly_inspector = RepoHealthAnomalyInspector()

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_anomaly_inspector_integration_with_pulse_engine(self):
        metric_value = random.uniform(10.0, 1000.0)
        anomaly_threshold = metric_value * random.uniform(0.1, 0.9)
        
        pulse_data = self.pulse_engine.collect_metrics(
            repo_id=self.repo_id,
            path=self.test_dir,
            base_metric=metric_value
        )
        
        self.assertIsNotNone(pulse_data)
        self.assertIn("metrics", pulse_data)

        inspection_result = self.anomaly_inspector.inspect(
            repo_id=self.repo_id,
            pulse_payload=pulse_data,
            threshold=anomaly_threshold
        )

        self.assertIsInstance(inspection_result, dict)
        self.assertEqual(inspection_result.get("repo_id"), self.repo_id)
        self.assertIn("is_anomaly", inspection_result)
        self.assertIn("deviation_score", inspection_result)
        self.assertTrue(inspection_result["is_anomaly"])

        log_record_id = str(uuid.uuid4())
        logged = self.logger.record_event(
            repo_id=self.repo_id,
            event_type="ANOMALY_INSPECTION",
            payload={"log_id": log_record_id, "result": inspection_result}
        )
        self.assertTrue(logged)

if __name__ == "__main__":
    unittest.main()