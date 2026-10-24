import unittest
import tempfile
import os
import uuid
import random

from skills.anomaly_audit_hub import AnomalyAuditHub, AnomalyAuditHubError


class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self.log_path = os.path.join(self.temp_dir.name, f"test_audit_integration_{uuid.uuid4().hex}.log")
        self.threshold = 10.0
        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_anomaly_audit_hub_end_to_end(self):
        self.hub.log_anomaly(
            source="integration_test_source",
            severity="HIGH",
            details={"msg": "integration test details"},
            telemetry_snapshot={"cpu": 95}
        )

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = 150.0

        aggregate_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )

        self.assertIsNotNone(aggregate_result)
        self.assertIsInstance(aggregate_result, (list, dict))

        final_report = self.hub.generate_final_report()
        self.assertIsNotNone(final_report)
        self.assertIsInstance(final_report, (list, dict))

    def test_multiple_anomaly_events_integration(self):
        for i in range(3):
            self.hub.log_anomaly(
                source=f"source_{i}",
                severity="CRITICAL",
                details={"step": i},
                telemetry_snapshot={"mem": 100 * i}
            )

        metric_name = "pipeline_latency"
        aggregate_result = self.hub.aggregate_and_report(metric_name, 200.0)
        self.assertIsNotNone(aggregate_result)

        report = self.hub.generate_final_report()
        self.assertIsNotNone(report)


if __name__ == "__main__":
    unittest.main()
