import unittest
import uuid
import random
import tempfile
import os
from skills.anomaly_correlator import AnomalyCorrelator, AnomalyCorrelatorError
from skills.anomaly_detector import AnomalyDetectorError

class TestAnomalyCorrelatorIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.temp_dir.name, f"test_log_{uuid.uuid4()}.json")
        self.correlator = AnomalyCorrelator(log_path=self.log_path, threshold=50.0)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_correlate_metric_integration_flow(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        random_value = float(random.randint(101, 500))

        is_anomaly = self.correlator.correlate_metric(metric_name, random_value)
        self.assertTrue(is_anomaly)

        events_data = self.correlator.correlate_events()
        self.assertGreaterEqual(events_data["correlated_count"], 1)
        
        report = self.correlator.get_correlation_report()
        self.assertIsNotNone(report)

    def test_correlate_metric_exception_handling_integration(self):
        metric_name = f"metric_err_{uuid.uuid4().hex[:8]}"
        random_value = random.randint(-1000, 1000)

        class BrokenDetector:
            def record_metric(self, name, val):
                raise AnomalyDetectorError("Simulated detector error for anti-cheat verification")
            def detect_anomaly(self, name, val):
                return False
            def analyze_execution_metrics(self, exec_id, payload):
                return {}

        broken_correlator = AnomalyCorrelator(detector=BrokenDetector(), log_path=self.log_path)

        with self.assertRaises(AnomalyCorrelatorError) as context:
            broken_correlator.correlate_metric(metric_name, random_value)
        
        self.assertIn("Simulated detector error", str(context.exception))

    def test_analyze_execution_flow_integration(self):
        execution_id = str(uuid.uuid4())
        payload = {
            f"param_{uuid.uuid4().hex[:4]}": random.random() for _ in range(3)
        }

        result = self.correlator.analyze_execution_flow(execution_id, payload)
        self.assertIsInstance(result, (dict, list, type(None)))

if __name__ == '__main__':
    unittest.main()