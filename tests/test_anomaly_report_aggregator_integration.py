import os
import random
import shutil
import tempfile
import unittest
import uuid

from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_report_aggregator import (
    AnomalyReportAggregator,
    AnomalyReportAggregatorError,
)


class TestAnomalyReportAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, f"test_anomalies_{uuid.uuid4().hex}.json")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_end_to_end_aggregation_and_reporting(self):
        aggregator = AnomalyReportAggregator(log_path=self.log_file)
        random_metric_name = f"latency_{uuid.uuid4().hex[:8]}"
        random_value = round(random.uniform(100.5, 999.9), 3)

        initial_report = aggregator.aggregate_and_report(random_metric_name, random_value)
        self.assertIsNotNone(initial_report)

        final_report = aggregator.generate_final_report()
        self.assertIsNotNone(final_report)

        dynamic_source = f"svc_{uuid.uuid4().hex[:6]}"
        dynamic_detail_id = f"evt_{uuid.uuid4().hex}"
        anomaly_payload = {
            "source": dynamic_source,
            "severity": "HIGH",
            "details": {"event_id": dynamic_detail_id, "score": random_value},
            "telemetry_snapshot": {"metric": random_metric_name}
        }
        aggregator._log_anomaly(anomaly_payload)

        updated_report = aggregator.generate_final_report()
        self.assertIsNotNone(updated_report)
        self.assertTrue(os.path.exists(self.log_file))

        with open(self.log_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(dynamic_source, content)
            self.assertIn(dynamic_detail_id, content)

    def test_execution_flow_aggregation_with_custom_logger(self):
        logger = AnomalyLogger(log_path=self.log_file)
        aggregator = AnomalyReportAggregator(logger=logger)

        execution_id = f"exec_{uuid.uuid4().hex}"
        random_cpu_val = str(round(random.uniform(85.0, 99.0), 2))
        random_mem_val = str(random.randint(4096, 8192))
        payload = {
            "cpu_usage": random_cpu_val,
            "memory_usage": random_mem_val,
            "trace_id": str(uuid.uuid4())
        }

        report = aggregator.aggregate_execution_flow(execution_id, payload)
        self.assertIsNotNone(report)
        self.assertIsInstance(payload["cpu_usage"], float)
        self.assertIsInstance(payload["memory_usage"], float)

        logged_anomalies = logger.get_anomalies()
        self.assertIsInstance(logged_anomalies, list)

    def test_aggregate_execution_flow_integration_with_non_numeric_fields(self):
        aggregator = AnomalyReportAggregator(log_path=self.log_file)
        execution_id = f"exec_{uuid.uuid4().hex}"
        payload = {
            "latency": "120.5",
            "throughput": "500",
            "service_name": "auth-service",
            "is_active": True
        }

        report = aggregator.aggregate_execution_flow(execution_id, payload)
        self.assertIsNotNone(report)
        self.assertIsInstance(payload["latency"], float)
        self.assertIsInstance(payload["throughput"], float)
        self.assertEqual(payload["service_name"], "auth-service")


if __name__ == "__main__":
    unittest.main()