import unittest
import uuid
import random
import os
from skills.incident_forensic_summarizer import incident_forensic_summarizer
from skills.incident_aggregator import incident_aggregator
from skills.system_health_telemetry_collector import system_health_telemetry_collector

class TestIncidentForensicSummarizerIntegration(unittest.TestCase):
    def test_forensic_summarizer_pipeline(self):
        unique_incident_id = f"inc-{uuid.uuid4()}"
        telemetry_metric_value = random.uniform(50.0, 500.0)
        
        telemetry_data = system_health_telemetry_collector(
            metric_id=str(uuid.uuid4()),
            load_value=telemetry_metric_value
        )
        
        incident_payload = incident_aggregator(
            incident_id=unique_incident_id,
            telemetry_payload=telemetry_data,
            severity_level=random.choice(["HIGH", "CRITICAL", "MEDIUM"])
        )
        
        summary_result = incident_forensic_summarizer(
            incident_data=incident_payload,
            include_telemetry_dump=True
        )
        
        self.assertIn("summary_id", summary_result)
        self.assertEqual(summary_result.get("target_incident_id"), unique_incident_id)
        self.assertIn(str(telemetry_metric_value), str(summary_result))
        
        report_path = summary_result.get("report_file_path")
        if report_path:
            self.assertTrue(os.path.exists(report_path))
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(unique_incident_id, content)

if __name__ == "__main__":
    unittest.main()