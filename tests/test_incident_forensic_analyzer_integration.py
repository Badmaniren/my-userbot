import unittest
import uuid
import random
import os
from skills.incident_forensic_analyzer import incident_forensic_analyzer
from skills.incident_aggregator import incident_aggregator
from skills.system_health_telemetry_collector import system_health_telemetry_collector
from skills.telemetry_processor import telemetry_processor

class TestIncidentForensicAnalyzerIntegration(unittest.TestCase):
    def test_forensic_analyzer_deep_retrospective_pipeline(self):
        unique_incident_id = str(uuid.uuid4())
        random_metric_value = random.uniform(10.0, 999.9)
        telemetry_source = f"node-{random.randint(100, 999)}"
        
        telemetry_data = system_health_telemetry_collector(
            source=telemetry_source,
            metric_val=random_metric_value
        )
        
        processed_telemetry = telemetry_processor(
            input_stream=telemetry_data
        )
        
        incident_record = incident_aggregator(
            incident_id=unique_incident_id,
            telemetry_ref=processed_telemetry
        )
        
        forensic_report_path = f"/tmp/forensic_report_{unique_incident_id}.json"
        
        analysis_result = incident_forensic_analyzer(
            incident_id=unique_incident_id,
            incident_payload=incident_record,
            output_path=forensic_report_path
        )
        
        self.assertEqual(analysis_result.get("target_incident_id"), unique_incident_id)
        self.assertTrue(os.path.exists(forensic_report_path))
        
        with open(forensic_report_path, "r", encoding="utf-8") as report_file:
            report_content = report_file.read()
            self.assertIn(unique_incident_id, report_content)
            self.assertIn(str(random_metric_value), report_content)
            
        if os.path.exists(forensic_report_path):
            os.remove(forensic_report_path)

if __name__ == "__main__":
    unittest.main()