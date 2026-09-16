import unittest
import uuid
import os
import json
import tempfile
from skills.incident_business_loss_reporter import incident_business_loss_reporter

class TestIncidentBusinessLossReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.reporter = incident_business_loss_reporter()
        self.incident_id = f"inc-{uuid.uuid4()}"
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_generate_report_integration(self):
        report = self.reporter.generate_report(self.incident_id)

        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("incident_id"), self.incident_id)
        self.assertIn("total_loss", report)
        self.assertIn("financial_metrics", report)
        self.assertIn("impact_metrics", report)
        self.assertTrue(report.get("is_generated"))

    def test_generate_report_with_export_integration(self):
        export_filename = f"report_{uuid.uuid4()}.json"
        export_path = os.path.join(self.temp_dir.name, export_filename)

        report = self.reporter.generate_report(self.incident_id, export_path=export_path)

        self.assertEqual(report.get("export_status"), "success")
        self.assertTrue(os.path.exists(export_path))

        with open(export_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data.get("incident_id"), self.incident_id)
        self.assertEqual(loaded_data.get("total_loss"), report.get("total_loss"))

    def test_generate_stream_report_integration(self):
        stream = self.reporter.generate_stream_report(self.incident_id)

        self.assertIsNotNone(stream)
        stream_content = stream.read()
        self.assertGreater(len(stream_content), 0)

        parsed_data = json.loads(stream_content.decode('utf-8'))
        self.assertEqual(parsed_data.get("incident_id"), self.incident_id)
        self.assertIn("financial_metrics", parsed_data)
        self.assertIn("impact_metrics", parsed_data)

if __name__ == "__main__":
    unittest.main()