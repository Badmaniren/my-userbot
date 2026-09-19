import unittest
import uuid
import random
import os
import tempfile
from skills.system_security_audit_log import system_security_audit_log
from skills.incident_aggregator import incident_aggregator
from skills.system_health_audit_pipeline import system_health_audit_pipeline

class TestSystemSecurityAuditLogIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.random_incident_id = f"inc-{uuid.uuid4()}"
        self.random_system_state = random.choice(["SECURE", "WARNING", "CRITICAL", "COMPROMISED"])
        self.random_severity = random.randint(1, 5)
        self.audit_log_path = os.path.join(self.test_dir.name, f"audit_{uuid.uuid4()}.log")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_security_audit_log_integration(self):
        incident_data = {
            "incident_id": self.random_incident_id,
            "severity": self.random_severity,
            "state": self.random_system_state,
            "metadata": {
                "source": "integration_test",
                "entropy": random.random()
            }
        }

        aggregated_incident = incident_aggregator(incident_data)
        
        system_health = system_health_audit_pipeline({
            "status": self.random_system_state,
            "metric_score": random.uniform(0.0, 100.0)
        })

        audit_payload = {
            "log_file": self.audit_log_path,
            "incident": aggregated_incident,
            "health_audit": system_health,
            "nonce": str(uuid.uuid4())
        }

        result = system_security_audit_log(audit_payload)

        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(self.audit_log_path), "Integration failed: Audit log file was not created.")
        
        with open(self.audit_log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
            self.assertIn(self.random_incident_id, log_content, "Audit log does not contain the generated incident ID.")

if __name__ == "__main__":
    unittest.main()