import unittest
import uuid
import random
import tempfile
import os
from skills.anomaly_correlator import AnomalyCorrelator, AnomalyCorrelatorError
from skills.anomaly_detector import AnomalyDetector
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyCorrelatorIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.temp_dir.name, f"test_log_{uuid.uuid4().hex}.json")
        self.correlator = AnomalyCorrelator(log_path=self.log_path, threshold=50.0)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_correlate_metric_and_events_integration(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        normal_value = float(random.randint(1, 40))
        anomaly_value = float(random.randint(51, 100))

        res_normal = self.correlator.correlate_metric(metric_name, normal_value)
        self.assertFalse(res_normal)

        res_anomaly = self.correlator.correlate_metric(metric_name, anomaly_value)
        self.assertTrue(res_anomaly)

        events_data = self.correlator.correlate_events()
        self.assertIn("correlated_count", events_data)
        self.assertIn("report", events_data)
        self.assertGreaterEqual(events_data["correlated_count"], 1)

        report = self.correlator.get_correlation_report()
        self.assertIsNotNone(report)

    def test_analyze_execution_flow_integration(self):
        execution_id = str(uuid.uuid4())
        metrics_payload = {
            f"cpu_usage_{uuid.uuid4().hex[:4]}": float(random.randint(10, 99)),
            f"memory_usage_{uuid.uuid4().hex[:4]}": float(random.randint(10, 99))
        }

        analysis_result = self.correlator.analyze_execution_flow(execution_id, metrics_payload)
        self.assertIsNotNone(analysis_result)

if __name__ == '__main__':
    unittest.main()