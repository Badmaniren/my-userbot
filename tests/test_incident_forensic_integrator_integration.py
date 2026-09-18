import unittest
import uuid
import random
import os
import tempfile
from skills.incident_forensic_integrator import (
    incident_aggregator,
    system_health_telemetry_collector,
    telemetry_processor,
    incident_impact_analyzer
)

class TestIncidentForensicIntegratorIntegration(unittest.TestCase):
    def test_end_to_end_forensic_aggregation(self):
        random_incident_id = f"inc-{uuid.uuid4()}"
        random_metric_value = random.uniform(100.0, 999.9)
        
        telemetry_data = system_health_telemetry_collector(
            metric_id=str(uuid.uuid4()),
            value=random_metric_value
        )
        
        processed_telemetry = telemetry_processor(telemetry_data)
        
        aggregated_incident = incident_aggregator(
            incident_id=random_incident_id,
            telemetry_payload=processed_telemetry
        )
        
        impact_report = incident_impact_analyzer(aggregated_incident)
        
        self.assertIn(random_incident_id, str(impact_report))
        self.assertTrue(isinstance(aggregated_incident, dict) or isinstance(aggregated_incident, str))
        
        temp_dir = tempfile.gettempdir()
        report_path = os.path.join(temp_dir, f"{random_incident_id}_forensic.log")
        
        with open(report_path, "w") as f:
            f.write(str(impact_report))
            
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r") as f:
            content = f.read()
            self.assertIn(random_incident_id, content)
            
        os.remove(report_path)

if __name__ == "__main__":
    unittest.main()