import unittest
import os
import shutil
import uuid
import random
from skills.dependency_audit_reporter import generate_dependency_audit_report, generate_audit_report

class TestDependencyAuditReporterIntegration(unittest.TestCase):

    def setUp(self):
        self.unique_id = str(uuid.uuid4())[:8]
        self.repo_path = os.path.abspath(f"./test_repo_{self.unique_id}")
        os.makedirs(self.repo_path, exist_ok=True)

        self.output_report_name = f"audit_report_{self.unique_id}.json"
        self.cve_identifier = f"CVE-2023-{random.randint(10000, 99999)}"
        self.target_version = f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.branch = f"feature/fix-{self.unique_id}"
        self.stream_source = f"source-{random.randint(1, 100)}"

    def tearDown(self):
        if os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path, ignore_errors=True)

        potential_report = os.path.join(self.repo_path, self.output_report_name)
        if os.path.exists(potential_report):
            os.remove(potential_report)

    def test_generate_dependency_audit_report_integration(self):
        result = generate_dependency_audit_report(
            repo_path=self.repo_path,
            output_report_name=self.output_report_name,
            cve_identifier=self.cve_identifier,
            target_version=self.target_version
        )

        self.assertIsInstance(result, dict)
        self.assertIn("report_path", result)
        self.assertIn("aggregation_data", result)
        self.assertIn("final_report", result)

        report_path = result["report_path"]
        self.assertTrue(os.path.exists(report_path), f"Report file was not created at {report_path}")

        aggregation_data = result["aggregation_data"]
        self.assertIsNotNone(aggregation_data)

        final_report = result["final_report"]
        self.assertIsInstance(final_report, str)
        self.assertTrue(len(final_report) > 0)

    def test_generate_audit_report_integration(self):
        final_report = generate_audit_report(
            repo_path=self.repo_path,
            branch=self.branch,
            stream_source=self.stream_source,
            output_report_name=self.output_report_name,
            cve_identifier=self.cve_identifier,
            target_version=self.target_version
        )

        self.assertIsInstance(final_report, str)
        self.assertTrue(len(final_report) > 0)

if __name__ == "__main__":
    unittest.main()