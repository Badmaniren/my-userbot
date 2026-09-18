import unittest
import uuid
import random
import os
import tempfile
from skills.incident_forensics_compliance_checker import IncidentComplianceChecker, check_incident_compliance

class TestIncidentForensicsComplianceCheckerIntegration(unittest.TestCase):
    def setUp(self):
        self.checker = IncidentComplianceChecker()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.destination_path = os.path.join(self.temp_dir.name, f"audit_{uuid.uuid4().hex}.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_evaluate_compliance_end_to_end(self):
        inc_id = f"INC-{uuid.uuid4().hex[:8]}"
        risk_val = random.randint(1, 15)
        
        incident_data = {
            "id": inc_id,
            "module_name": "auth_service",
            "exception": "TokenExpiredError",
            "traceback_str": "Traceback (most recent call last):\n  File 'auth.py', line 42"
        }
        
        financial_data = {
            "risk_score": risk_val,
            "estimated_loss": random.uniform(100.0, 5000.0)
        }

        result = check_incident_compliance(
            incident_data=incident_data,
            destination_path=self.destination_path,
            include_raw_telemetry=True,
            financial_data=financial_data,
            format_type="json"
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), inc_id)
        
        expected_compliant = risk_val < 10
        self.assertEqual(result.get("compliant"), expected_compliant)
        self.assertEqual(result.get("compliance_status"), "COMPLIANT" if expected_compliant else "NON_COMPLIANT")
        
        audit_trail = result.get("audit_trail")
        self.assertIsInstance(audit_trail, dict)
        
        forensics_report = result.get("forensics_report")
        self.assertIsInstance(forensics_report, dict)
        
        risk_assessment = result.get("risk_assessment")
        self.assertEqual(risk_assessment.get("score"), risk_val)
        
        self.assertTrue(os.path.exists(self.destination_path))

    def test_stream_compliance_package_integration(self):
        inc_id = f"INC-{uuid.uuid4().hex[:8]}"
        financial_data = {
            "risk_score": random.randint(0, 5)
        }

        stream_result = self.checker.stream_compliance_package(
            incident_id=inc_id,
            financial_data=financial_data,
            format_type="json"
        )

        self.assertIsNotNone(stream_result)

if __name__ == "__main__":
    unittest.main()