import unittest
import os
import uuid
import random
from skills.incident_audit_trail_collector import collect_incident_audit_trail

class TestIncidentAuditTrailCollectorIntegration(unittest.TestCase):
    def test_collect_incident_audit_trail_integration(self):
        rand_id = f"INC-{uuid.uuid4()}"
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        rand_severity = random.choice(severities)
        rand_telemetry_key = f"metric_{uuid.uuid4().hex[:6]}"
        rand_telemetry_val = random.randint(100, 999)
        
        incident_data = {
            "incident_id": rand_id,
            "severity": rand_severity,
            "source_telemetry": {
                rand_telemetry_key: rand_telemetry_val
            }
        }
        
        dest_dir = f"test_audit_logs_{uuid.uuid4().hex}"
        destination_path = os.path.join(dest_dir, "audit_trail.log")
        
        try:
            result = collect_incident_audit_trail(
                incident_data=incident_data,
                destination_path=destination_path,
                include_raw_telemetry=True
            )
            
            self.assertEqual(result.get("status"), "SUCCESS")
            self.assertEqual(result.get("logged_incident_id"), rand_id)
            
            self.assertTrue(os.path.exists(destination_path), "Файл аудиторского следа не был создан")
            
            with open(destination_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            self.assertIn(f"INCIDENT_ID: {rand_id}", content)
            self.assertIn(f"SEVERITY: {rand_severity}", content)
            self.assertIn(rand_telemetry_key, content)
            self.assertIn(str(rand_telemetry_val), content)
            
        finally:
            if os.path.exists(destination_path):
                os.remove(destination_path)
            if os.path.exists(dest_dir):
                os.rmdir(dest_dir)

if __name__ == "__main__":
    unittest.main()