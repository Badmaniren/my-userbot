import unittest
import uuid
import random
import os
import tempfile
from skills.incident_forensics_security_auditor import (
    incident_forensics_compliance_checker,
    incident_forensics_report_bridge,
    incident_forensics_synthesizer
)

class TestIncidentForensicsSecurityAuditorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.random_audit_id = str(uuid.uuid4())
        self.random_incident_id = str(uuid.uuid4())
        self.random_log_entries = [
            f"TIMESTAMP: {random.randint(100000, 999999)} | EVENT: UNAUTHORIZED_ACCESS | ID: {uuid.uuid4()}",
            f"TIMESTAMP: {random.randint(100000, 999999)} | EVENT: INTEGRITY_CHECK_FAILED | ID: {uuid.uuid4()}"
        ]
        self.log_file_path = os.path.join(self.test_dir.name, f"forensics_{self.random_audit_id}.log")
        with open(self.log_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(self.random_log_entries))

    def tearDown(self):
        self.test_dir.cleanup()

    def test_forensics_security_auditor_real_integration(self):
        input_payload = {
            "audit_id": self.random_audit_id,
            "incident_id": self.random_incident_id,
            "log_path": self.log_file_path,
            "tampering_threshold": random.uniform(0.1, 0.9)
        }

        compliance_result = incident_forensics_compliance_checker(input_payload)

        self.assertIsInstance(compliance_result, dict)
        self.assertIn("compliant", compliance_result)

        bridge_payload = {
            "audit_id": self.random_audit_id,
            "compliance_data": compliance_result,
            "source_log": self.log_file_path
        }

        bridge_result = incident_forensics_report_bridge(bridge_payload)
        self.assertIsInstance(bridge_result, dict)

        synthesizer_payload = {
            "audit_id": self.random_audit_id,
            "incident_id": self.random_incident_id,
            "bridge_data": bridge_result,
            "output_format": "json"
        }

        final_report = incident_forensics_synthesizer(synthesizer_payload)

        self.assertIsInstance(final_report, dict)
        self.assertEqual(final_report.get("audit_id"), self.random_audit_id)
        self.assertEqual(final_report.get("incident_id"), self.random_incident_id)

        expected_artifact_path = os.path.join(self.test_dir.name, f"audit_report_{self.random_audit_id}.json")
        self.assertTrue(
            os.path.exists(expected_artifact_path) or "report_path" in final_report,
            "Integration must produce a verifiable report file or path trace."
        )

if __name__ == "__main__":
    unittest.main()