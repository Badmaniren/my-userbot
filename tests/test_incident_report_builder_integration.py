import unittest
import os
import uuid
from skills.incident_report_builder import IncidentReportBuilder

class TestIncidentReportBuilderIntegration(unittest.TestCase):
    def setUp(self):
        self.builder = IncidentReportBuilder()
        self.random_metric_payload = {
            "incident_id": str(uuid.uuid4()),
            "status": "success",
            "metric_value": 42.5
        }
        self.random_audit_data = {
            "dependency": f"pkg-{uuid.uuid4()}",
            "vulnerability_level": "high"
        }
        self.random_epic_id = f"EPIC-{uuid.uuid4()}"
        self.random_stream_data = f"stream-data-{uuid.uuid4()}"
        self.module_name = f"mod_{uuid.uuid4().hex[:8]}"
        self.output_path = f"test_report_{uuid.uuid4()}.txt"
        self.export_format = "json"

    def tearDown(self):
        if os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except OSError:
                pass

    def test_build_report_integration(self):
        result = self.builder.build_report(self.random_metric_payload, self.random_audit_data)
        self.assertIsInstance(result, str)
        self.assertIn(str(self.random_metric_payload.get("incident_id")), result)

    def test_export_analytics_integration(self):
        result = self.builder.export_analytics(
            self.random_epic_id, 
            self.random_stream_data, 
            self.export_format
        )
        self.assertIsInstance(result, str)

    def test_generate_epic_incident_pipeline_integration(self):
        result = self.builder.generate_epic_incident_pipeline(
            self.module_name, 
            self.random_audit_data, 
            self.output_path
        )
        self.assertIsInstance(result, bool)

    def test_export_raw_metrics_integration(self):
        result = self.builder.export_metrics(self.output_path, self.export_format)
        self.assertIsInstance(result, bool)

    def test_export_incident_report_file_creation(self):
        summary_payload = f"Summary data {uuid.uuid4()}"
        success = self.builder.export_incident_report(summary_payload, self.output_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.output_path))
        
        with open(self.output_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, str(summary_payload))

if __name__ == "__main__":
    unittest.main()