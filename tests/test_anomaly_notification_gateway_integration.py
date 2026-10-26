import unittest
import uuid
import random
import tempfile
import os
from skills.anomaly_notification_gateway import (
    route_and_format_notification,
    start_new,
    AnomalyAuditHub,
    AnomalyLogger
)

class TestAnomalyNotificationGatewayIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.temp_dir.name, f"audit_{uuid.uuid4().hex}.json")
        self.repo_path = self.temp_dir.name
        self.threshold = random.uniform(0.5, 9.5)

        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        self.logger = AnomalyLogger(log_path=self.log_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_gateway_integration_flow(self):
        source_id = f"service_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_value = random.uniform(0.0, 10.0)
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"

        raw_details = {
            "error_code": random.randint(1000, 9999),
            "message": f"Random anomaly generated: {uuid.uuid4()}",
            "trace_id": str(uuid.uuid4())
        }

        telemetry_snapshot = {
            "cpu_load": random.randint(10, 100),
            "memory_usage": random.randint(20, 99),
            "metric_value": metric_value
        }

        filter_result = start_new(raw_details)

        self.audit_hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=raw_details,
            telemetry_snapshot=telemetry_snapshot
        )

        aggregated_report = self.audit_hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )

        final_report = self.audit_hub.generate_final_report()

        gateway_payload = {
            "source": source_id,
            "severity": severity_level,
            "details": raw_details,
            "telemetry": telemetry_snapshot,
            "filter_data": filter_result,
            "aggregated": aggregated_report,
            "report_summary": final_report
        }

        notification_result = route_and_format_notification(gateway_payload)

        self.assertIsNotNone(notification_result)
        self.assertIn("formatted_message", notification_result)
        self.assertIn(source_id, notification_result["formatted_message"])
        self.assertIn(severity_level, notification_result["formatted_message"])

        logged_anomalies = self.logger.get_anomalies()
        self.assertTrue(any(a.get("source") == source_id for a in logged_anomalies))

        structured_report = self.logger.get_structured_report()
        self.assertIsInstance(structured_report, dict)

        self.assertTrue(os.path.exists(self.log_path))

if __name__ == "__main__":
    unittest.main()
