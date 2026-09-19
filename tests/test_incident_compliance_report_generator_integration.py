import unittest
import uuid
import random
import os
from datetime import datetime

from skills.incident_compliance_report_generator import generate_compliance_report
from skills.incident_aggregator import aggregate_incidents
from skills.incident_audit_trail_collector import collect_audit_trail

class TestIncidentComplianceReportGeneratorIntegration(unittest.TestCase):
    def test_compliance_report_generation_integration(self):
        unique_run_id = str(uuid.uuid4())
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        incident_count = random.randint(3, 10)
        
        raw_incidents = []
        for _ in range(incident_count):
            inc_id = str(uuid.uuid4())
            raw_incidents.append({
                "incident_id": inc_id,
                "run_id": unique_run_id,
                "severity": severity_level,
                "timestamp": datetime.utcnow().isoformat(),
                "description": f"Integration test incident {inc_id}"
            })
            
        aggregated_data = aggregate_incidents(raw_incidents)
        self.assertIsNotNone(aggregated_data, "Incident aggregator failed to return data.")
        
        audit_trail = collect_audit_trail(unique_run_id)
        self.assertIsNotNone(audit_trail, "Audit trail collector failed to return data.")
        
        report_output_path = f"/tmp/compliance_report_{unique_run_id}.json"
        
        generation_result = generate_compliance_report(
            aggregated_incidents=aggregated_data,
            audit_trail=audit_trail,
            output_path=report_output_path,
            metadata={"run_id": unique_run_id, "random_factor": random.random()}
        )
        
        self.assertTrue(generation_result, "Compliance report generator returned False or failure status.")
        self.assertTrue(os.path.exists(report_output_path), "Integration failure: Report file was not created on disk.")
        
        with open(report_output_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(unique_run_id, content, "Generated report does not contain the unique run ID, indicating potential hardcoding or data loss.")

if __name__ == "__main__":
    unittest.main()