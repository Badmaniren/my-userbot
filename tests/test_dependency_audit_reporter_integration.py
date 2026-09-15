import unittest
import os
import json
import uuid
import random
from io import BytesIO
from skills.dependency_audit_reporter import DependencyAuditReporter
from skills.package_requirement_reader import PyPIClient

class TestDependencyAuditReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.reporter = DependencyAuditReporter()
        self.pypi_client = PyPIClient("https://pypi.org")
        self.epic_id = str(uuid.uuid4())
        self.output_filename = f"epic_{self.epic_id}_audit.log"
        self.report_filepath = f"epic_{self.epic_id}_summary.json"

    def tearDown(self):
        for path in [self.output_filename, self.report_filepath]:
            if os.path.exists(path):
                os.remove(path)

    def test_full_audit_and_epic_workflow_integration(self):
        random_vulnerabilities_count = random.randint(1, 10)
        random_package = f"test-pkg-{uuid.uuid4()}"
        random_version = f"{random.randint(0, 2)}.{random.randint(0, 9)}.{random.randint(0, 9)}"

        audit_payload = {
            "epic_id": self.epic_id,
            "target_package": random_package,
            "version": random_version,
            "vulnerabilities_found": random_vulnerabilities_count
        }

        report_str = self.reporter.generate_report(audit_payload)
        parsed_report = json.loads(report_str)
        
        self.assertEqual(parsed_report["epic_id"], self.epic_id)
        self.assertEqual(parsed_report["target_package"], random_package)
        self.assertEqual(parsed_report["vulnerabilities_found"], random_vulnerabilities_count)
        self.assertIn("timestamp", parsed_report)

        summary_payload = {
            "status": "COMPLETED",
            "audit_summary": parsed_report
        }
        exported_summary_str = self.reporter.export_summary(summary_payload, format="json")
        
        stream_data = exported_summary_str.encode("utf-8")
        stream = BytesIO(stream_data)

        finalize_result = self.reporter.finalize_epic(self.epic_id, stream)
        self.assertTrue(finalize_result)
        self.assertTrue(os.path.exists(self.output_filename))

        with open(self.output_filename, "rb") as f:
            file_content = f.read().decode("utf-8")
        
        reloaded_summary = json.loads(file_content)
        self.assertEqual(reloaded_summary["status"], "COMPLETED")
        self.assertEqual(reloaded_summary["audit_summary"]["epic_id"], self.epic_id)

        epic_report_payload = {
            "epic": self.epic_id,
            "metrics": {
                "scanned_dependencies": random.randint(5, 50),
                "issues": random_vulnerabilities_count
            }
        }
        
        report_written = self.reporter.generate_epic_report(epic_report_payload, self.report_filepath)
        self.assertTrue(report_written)
        self.assertTrue(os.path.exists(self.report_filepath))

        with open(self.report_filepath, "r", encoding="utf-8") as f:
            written_data = json.load(f)
            
        self.assertEqual(written_data["epic"], self.epic_id)
        self.assertEqual(written_data["metrics"]["issues"], random_vulnerabilities_count)

if __name__ == "__main__":
    unittest.main()