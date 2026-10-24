import os
import random
import tempfile
import unittest
import uuid
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHubIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = os.path.join(self.temp_dir.name, "test_repo")
        os.makedirs(self.repo_path, exist_ok=True)
        self.log_path = os.path.join(
            self.temp_dir.name, f"audit_{uuid.uuid4().hex}.log"
        )
        self.threshold = random.uniform(10.0, 100.0)
        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_log_anomaly_integration(self):
        source = f"service_{uuid.uuid4().hex[:8]}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        unique_token = uuid.uuid4().hex
        details = {
            "token": unique_token,
            "metric_val": random.randint(100, 999),
        }
        telemetry_snapshot = {"cpu_usage": random.uniform(0.0, 100.0)}

        result = self.hub.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot,
        )

        self.assertIsNotNone(result)

        if os.path.exists(self.log_path):
            with open(self.log_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(source, content)
                self.assertIn(unique_token, content)

    def test_aggregate_and_report_integration(self):
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        value = self.threshold + random.uniform(1.0, 50.0)

        agg_result = self.hub.aggregate_and_report(
            metric_name=metric_name, value=value
        )
        self.assertIsNotNone(agg_result)

        final_report = self.hub.generate_final_report()
        self.assertIsNotNone(final_report)

    def test_full_pipeline_without_mocks(self):
        num_records = random.randint(2, 5)
        generated_sources = []

        for _ in range(num_records):
            source = f"src_{uuid.uuid4().hex[:6]}"
            generated_sources.append(source)
            self.hub.log_anomaly(
                source=source,
                severity="WARNING",
                details={"param": uuid.uuid4().hex},
                telemetry_snapshot={"mem": random.uniform(10.0, 90.0)},
            )

        metric_name = f"latency_{uuid.uuid4().hex[:6]}"
        self.hub.aggregate_and_report(
            metric_name=metric_name, value=random.uniform(0.1, 500.0)
        )

        report = self.hub.generate_final_report()
        self.assertIsNotNone(report)

        if os.path.exists(self.log_path):
            with open(self.log_path, "r", encoding="utf-8") as f:
                log_contents = f.read()
                for src in generated_sources:
                    self.assertIn(src, log_contents)


if __name__ == "__main__":
    unittest.main()