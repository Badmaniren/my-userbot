import unittest
import uuid
import random
from skills.anomaly_correlator import AnomalyCorrelator, AnomalyCorrelatorError
from skills.anomaly_detector import AnomalyDetector
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyCorrelatorIntegration(unittest.TestCase):
    def setUp(self):
        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.anomaly_value = float(random.randint(100, 1000))
        self.normal_value = float(random.randint(1, 10))
        
        self.correlator = AnomalyCorrelator(threshold=50.0)

    def test_correlate_metric_integration_flow(self):
        is_normal_detected = self.correlator.correlate_metric(self.metric_name, self.normal_value)
        self.assertFalse(is_normal_detected, "Normal value should not trigger an anomaly detection.")

        is_anomaly_detected = self.correlator.correlate_metric(self.metric_name, self.anomaly_value)
        self.assertTrue(is_anomaly_detected, "Value exceeding threshold should trigger an anomaly detection.")

        correlation_results = self.correlator.correlate_events()
        self.assertGreaterEqual(
            correlation_results["correlated_count"],
            1,
            "Correlated count should reflect logged anomalies from the live detector and logger."
        )

        report = self.correlator.get_correlation_report()
        self.assertIsNotNone(report, "Structured report must not be None after correlating events.")

    def test_execution_flow_analysis_integration(self):
        execution_id = str(uuid.uuid4())
        metrics_payload = {
            f"cpu_load_{uuid.uuid4().hex[:4]}": float(random.randint(80, 100)),
            f"memory_usage_{uuid.uuid4().hex[:4]}": float(random.randint(90, 100))
        }

        analysis_result = self.correlator.analyze_execution_flow(execution_id, metrics_payload)
        self.assertIsInstance(
            analysis_result,
            (dict, list, bool),
            "Analysis execution flow must return a processed structure from the detector."
        )

if __name__ == "__main__":
    unittest.main()