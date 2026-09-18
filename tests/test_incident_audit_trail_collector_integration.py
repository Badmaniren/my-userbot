import unittest
import uuid
import random
import os
import tempfile
from skills.incident_audit_trail_collector import collect_incident_audit_trail
from skills.incident_aggregator import aggregate_incidents
from skills.system_health_telemetry_collector import collect_telemetry

class TestIncidentAuditTrailCollectorIntegration(unittest.TestCase):
    def test_audit_trail_collection_real_flow(self):
        random_seed = random.randint(1000, 9999)
        incident_id = f"INC-{uuid.uuid4()}"
        component_name = f"service-node-{random_seed}"
        error_code = random.choice([500, 502, 503, 504])
        
        telemetry_data = collect_telemetry(
            component=component_name,
            metric="error_rate",
            value=float(error_code)
        )
        
        aggregated_incident = aggregate_incidents(
            incident_id=incident_id,
            source_telemetry=telemetry_data,
            severity="CRITICAL"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file_path = os.path.join(temp_dir, f"audit_{incident_id}.log")
            
            audit_result = collect_incident_audit_trail(
                incident_data=aggregated_incident,
                destination_path=output_file_path,
                include_raw_telemetry=True
            )
            
            self.assertTrue(os.path.exists(output_file_path), "Audit trail log file was not created.")
            
            with open(output_file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
                
            self.assertIn(incident_id, file_content, "Generated incident ID is missing from the audit log.")
            self.assertIn(str(error_code), file_content, "Telemetry error code is missing from the audit log.")
            
            self.assertIsInstance(audit_result, dict)
            self.assertEqual(audit_result.get("status"), "SUCCESS")
            self.assertEqual(audit_result.get("logged_incident_id"), incident_id)

if __name__ == "__main__":
    unittest.main()