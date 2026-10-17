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
        
        self.threshold = random.uniform(10.0, 50.0)
        self.correlator = AnomalyCorrelator(
            log_path=self.temp_log_file.name,
            threshold=self.threshold
        )

    def tearDown(self):
        if os.path.exists(self.temp_log_file.name):
            os.unlink(self.temp_log_file.name)

    def test_correlate_metric_integration_flow(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        normal_value = self.threshold / 2.0
        anomalous_value = self.threshold * 3.0

        is_anomaly_normal = self.correlator.correlate_metric(metric_name, normal_value)
        self.assertFalse(is_anomaly_normal)

        is_anomaly_high = self.correlator.correlate_metric(metric_name, anomalous_value)
        self.assertTrue(is_anomaly_high)

        events = self.correlator.correlate_events()
        self.assertGreaterEqual(events["correlated_count"], 1)
        
        report = events["report"]
        self.assertIsInstance(report, (dict, list, str))

    def test_analyze_execution_flow_integration(self):
        execution_id = f"exec_{uuid.uuid4().hex}"
        random_metric_val = random.uniform(1.0, 100.0)
        metrics_payload = {
            f"cpu_load_{uuid.uuid4().hex[:4]}": random_metric_val,
            f"memory_usage_{uuid.uuid4().hex[:4]}": random_metric_val * 2
        }

        analysis_result = self.correlator.analyze_execution_flow(execution_id, metrics_payload)
        self.assertIsInstance(analysis_result, dict)

    def test_correlation_report_structure(self):
        metric_name = f"error_rate_{uuid.uuid4().hex[:6]}"
        extreme_value = random.uniform(500.0, 1000.0)

        self.correlator.correlate_metric(metric_name, extreme_value)
        
        report = self.correlator.get_correlation_report()
        self.assertIsNotNone(report)

        events_data = self.correlator.correlate_events()
        self.assertIn("correlated_count", events_data)
        self.assertIn("report", events_data)

    def test_end_to_end_anomaly_correlation_flow(self):
        raw_data = {
            "source": "integration_test_service",
            "severity": "CRITICAL",
            "details": "Critical memory threshold exceeded",
            "telemetry_snapshot": {
                "memory_usage": 98.5,
                "swap_usage": 45.2
            }
        }

        result = self.correlator.correlate(raw_data)

        self.assertIsInstance(result, dict)
        self.assertIn("filtered_data", result)
        self.assertIn("correlated_count", result)
        self.assertIn("report", result)
        self.assertIn("visualization", result)
        self.assertGreaterEqual(result["correlated_count"], 1)
        self.assertEqual(result["filtered_data"]["source"], "integration_test_service")
        self.assertEqual(result["filtered_data"]["severity"], "CRITICAL")


if __name__ == "__main__":
    unittest.main()