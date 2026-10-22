import unittest
import tempfile
import shutil
import uuid
import random
import os

from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_report_aggregator import AnomalyReportAggregatorError


class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, f"audit_{uuid.uuid4()}.log")
        self.repo_path = self.test_dir
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_end_to_end_anomaly_pipeline(self):
        source_id = f"source_{uuid.uuid4()}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(0.0, 100.0), 2)

        details = {
            "error_code": random.randint(1000, 9999),
            "message": f"Test anomaly failure {uuid.uuid4()}"
        }
        telemetry_snapshot = {
            "cpu_load": round(random.uniform(10.0, 99.9), 2),
            "memory_usage": round(random.uniform(20.0, 90.0), 2)
        }

        log_result = self.hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.assertIsNotNone(log_result)

        aggregation_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )

        self.assertIsNotNone(aggregation_result)

        final_report = self.hub.generate_final_report()
        self.assertIsInstance(final_report, (dict, list, str))

        self.assertTrue(os.path.exists(self.log_file))
        with open(self.log_file, "r", encoding="utf-8") as f:
            log_contents = f.read()
            self.assertIn(source_id, log_contents)
            self.assertIn(severity_level, log_contents)

    def test_exception_propagation_without_suppression(self):
        invalid_metric_name = ""
        invalid_value = float('nan')

        with self.assertRaises((AnomalyReportAggregatorError, ValueError, TypeError)):
            self.hub.aggregate_and_report(
                metric_name=invalid_metric_name,
                value=invalid_value
            )


if __name__ == "__main__":
    unittest.main()