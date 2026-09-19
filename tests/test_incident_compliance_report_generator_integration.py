import unittest
import uuid
import random
import os
import json
from skills import incident_compliance_report_generator

class TestIncidentComplianceReportGeneratorIntegration(unittest.TestCase):
    def test_start_new_and_generate_report_integration(self):
        rand_suffix = random.randint(10000, 99999)
        incident_id = f"INC-{rand_suffix}"
        standard = f"ISO-{random.randint(20000, 29999)}"
        report_format = "json"
        
        output_path = f"./test_outputs/compliance_report_{rand_suffix}.json"
        
        try:
            result = incident_compliance_report_generator.start_new(
                incident_id=incident_id,
                standard=standard,
                report_format=report_format,
                export_to_stream=True
            )
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("incident_id"), incident_id)
            self.assertEqual(result.get("standard"), standard)
            self.assertIn("report_id", result)
            self.assertIsNotNone(result.get("report_id"))
            
            aggregated_data = {"incident_id": incident_id, "status": "processed"}
            audit_trail_data = [{"event": "check", "id": rand_suffix}]
            
            generation_success = incident_compliance_report_generator.generate_compliance_report(
                aggregated_incidents=aggregated_data,
                audit_trail=audit_trail_data,
                output_path=output_path,
                metadata={"test_run": rand_suffix}
            )
            
            self.assertTrue(generation_success)
            self.assertTrue(os.path.exists(output_path))
            
            with open(output_path, "r", encoding="utf-8") as f:
                file_content = json.load(f)
                
            self.assertEqual(file_content["aggregated_incidents"]["incident_id"], incident_id)
            self.assertEqual(file_content["metadata"]["test_run"], rand_suffix)
            
        finally:
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                    os.rmdir(os.path.dirname(output_path))
                except OSError:
                    pass

if __name__ == "__main__":
    unittest.main()