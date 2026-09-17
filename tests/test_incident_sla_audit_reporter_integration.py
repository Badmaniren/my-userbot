import unittest
import uuid
import random
import io
from skills.incident_sla_audit_reporter import incident_sla_audit_reporter, IncidentSlaAuditReporter


class TestIncidentSlaAuditReporterIntegration(unittest.TestCase):

    def test_incident_sla_audit_reporter_functional_payload(self):
        random_id = f"INC-{random.randint(10000, 99999)}"
        payload = {"incident_id": random_id}

        result = incident_sla_audit_reporter(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), random_id)
        self.assertIn("audit_id", result)
        self.assertIn("audit_timestamp", result)
        self.assertIn("sla_compliant", result)
        self.assertIn("compliance_score", result)

    def test_class_instantiation_and_single_audit(self):
        random_id = f"INC-{random.randint(100000, 999999)}"
        reporter = IncidentSlaAuditReporter(audit_context={"env": "integration-test"})
        report = reporter.generate_audit_report(random_id)

        self.assertIsInstance(report, dict)
        self.assertEqual(report["incident_id"], random_id)
        self.assertTrue(len(report["audit_id"]) > 0)
        self.assertIn("target_hours", report)
        self.assertIn("actual_hours", report)
        self.assertIn("deviation_factor", report)

    def test_export_report_stream(self):
        random_id = f"INC-{random.randint(1000, 9999)}"
        reporter = IncidentSlaAuditReporter()
        stream = io.BytesIO()

        success = reporter.export_report_stream(random_id, stream)
        self.assertTrue(success)

        stream.seek(0)
        content = stream.read()
        self.assertTrue(len(content) > 0)

    def test_batch_audit_compliance(self):
        random_ids = [f"INC-{random.randint(1000, 9999)}" for _ in range(3)]
        reporter = IncidentSlaAuditReporter()

        batch_result = reporter.batch_audit_compliance(random_ids)

        self.assertIsInstance(batch_result, dict)
        self.assertEqual(batch_result["total_evaluated"], 3)
        self.assertIn("compliance_rate", batch_result)
        self.assertEqual(len(batch_result["details"]), 3)


if __name__ == "__main__":
    unittest.main()