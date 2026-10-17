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
        self.temp_log_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_log_file.close()
        
        self.logger = AnomalyLogger(log_path=self.temp_log_file.name)
        self.detector = AnomalyDetector()
        self.correlator = AnomalyCorrelator(
            detector=self.detector,
            logger=self.logger,
            threshold=25.0
        )

    def tearDown(self):
        if os.path.exists(self.temp_log_file.name):
            os.remove(self.temp_log_file.name)

    def test_correlate_metric_real_integration(self):
        unique_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        anomaly_value = float(random.randint(51, 100))
        normal_value = float(random.randint(1, 49))

        is_normal_detected = self.correlator.correlate_metric(unique_metric_name, normal_value)
        self.assertFalse(is_normal_detected)

        is_anomaly_detected = self.correlator.correlate_metric(unique_metric_name, anomaly_value)
        self.assertTrue(is_anomaly_detected)

        report = self.correlator.get_correlation_report()
        self.assertIsInstance(report, (dict, list, str))

        events = self.correlator.correlate_events()
        self.assertIn("correlated_count", events)
        self.assertGreaterEqual(events["correlated_count"], 1)

    def test_analyze_execution_flow_integration(self):
        unique_execution_id = f"exec_{uuid.uuid4().hex}"
        payload_data = {
            f"cpu_load_{random.randint(1, 100)}": random.uniform(10.0, 99.0),
            f"memory_usage_{random.randint(1, 100)}": random.uniform(20.0, 90.0)
        }

        analysis_result = self.correlator.analyze_execution_flow(unique_execution_id, payload_data)
        self.assertIsNotNone(analysis_result)

    def test_correlator_error_handling_chain(self):
        invalid_metric_name = f"err_metric_{uuid.uuid4().hex[:6]}"
        invalid_value = "non_numeric_random_data"

        with self.assertRaises((AnomalyCorrelatorError, TypeError, ValueError)):
            self.correlator.correlate_metric(invalid_metric_name, invalid_value)


if __name__ == "__main__":
    unittest.main()