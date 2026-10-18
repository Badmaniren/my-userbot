import unittest
import os
import tempfile
import uuid
import random
from skills.anomaly_security_gateway import AnomalySecurityGateway
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_filter import AnomalyFilter


class TestAnomalySecurityGatewayIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.log_path = os.path.join(self.repo_path, f"audit_{uuid.uuid4()}.log")
        self.threshold = random.randint(1, 100)

        self.gateway = AnomalySecurityGateway(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_gateway_composition_integration(self):
        self.assertIsInstance(self.gateway.audit_hub, AnomalyAuditHub)
        self.assertIsInstance(self.gateway.filter_module, AnomalyFilter)

        unique_source = f"source_{uuid.uuid4()}"
        random_severity = random.randint(1, 10)
        random_value = random.uniform(10.0, 1000.0)
        metric_name = f"metric_{uuid.uuid4()}"

        raw_data = {
            "id": str(uuid.uuid4()),
            "source": unique_source,
            "severity": random_severity,
            "details": f"Random details {uuid.uuid4()}",
            "metric": random_value
        }

        filtered_result = self.gateway.process_and_filter(raw_data)
        self.assertIsNotNone(filtered_result)

        self.gateway.audit_hub.log_anomaly(
            source=unique_source,
            severity=random_severity,
            details=raw_data["details"],
            telemetry_snapshot={"cpu": random.randint(0, 100)}
        )

        self.gateway.audit_hub.aggregate_and_report(metric_name, random_value)
        report = self.gateway.audit_hub.generate_final_report()

        self.assertIsNotNone(report)
        self.assertTrue(os.path.exists(self.log_path))


if __name__ == "__main__":
    unittest.main()