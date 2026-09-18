import unittest
import uuid
import random
import tempfile
import os
from skills.incident_forensics_compliance_checker import IncidentComplianceChecker, check_incident_compliance

class TestIncidentComplianceCheckerIntegration(unittest.TestCase):
    def setUp(self):
        self.checker = IncidentComplianceChecker()
        self.temp_dir = tempfile.TemporaryDirectory()
        
    def tearDown(self):
        self.temp_dir.cleanup()

    def test_evaluate_compliance_real_integration(self):
        rand_id = f"inc-{uuid.uuid4()}"
        risk_value = random.randint(0, 15)
        destination_file = os.path.join(self.temp_dir.name, f"audit_{uuid.uuid4()}.json")
        
        incident_data = {
            "id": rand_id,
            "module_name": "integration_test_module",
            "exception": "TestException",
            "traceback_str": "Traceback mock..."
        }
        
        financial_data = {
            "risk_score": risk_value,
            "estimated_loss": random.uniform(100.0, 5000.0)
        }

        result = self.checker.evaluate_compliance(
            incident_data=incident_data,
            destination_path=destination_file,
            include_raw_telemetry=True,
            financial_data=financial_data,
            export_path=None,
            format_type="json"
        )

        self.assertEqual(result["incident_id"], rand_id)
        self.assertEqual(result["risk_assessment"]["score"], risk_value)
        
        expected_compliant = risk_value < 10
        self.assertEqual(result["compliant"], expected_compliant)
        self.assertEqual(result["compliance_status"], "COMPLIANT" if expected_compliant else "NON_COMPLIANT")
        
        self.assertIn("audit_trail", result)
        self.assertIn("forensics_report", result)
        
        self.assertTrue(os.path.exists(destination_file))

    def test_check_incident_compliance_standalone_function(self):
        rand_id = str(uuid.uuid4())
        risk_value = random.choice([5, 12])
        
        result = check_incident_compliance(
            incident_id=rand_id,
            financial_data={"risk_score": risk_value}
        )
        
        self.assertEqual(result["incident_id"], rand_id)
        self.assertEqual(result["risk_assessment"]["score"], risk_value)
        self.assertIsInstance(result["compliant"], bool)

if __name__ == "__main__":
    unittest.main()