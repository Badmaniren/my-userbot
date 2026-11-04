import unittest
import os
import tempfile
import uuid
import random
import json

from skills import dependency_audit_aggregator
import vulnerability_analyzer
import dependency_updater_pipeline
import repo_reporter


class TestDependencyAuditAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.random_pkg = f"pkg-{uuid.uuid4().hex[:8]}"
        self.random_version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.cve_id = f"CVE-{random.randint(2000, 2024)}-{random.randint(1000, 9999)}"
        
        self.req_path = os.path.join(self.repo_path, "requirements.txt")
        with open(self.req_path, "w", encoding="utf-8") as f:
            f.write(f"{self.random_pkg}=={self.random_version}\n")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_aggregate_dependencies_integration(self):
        report_filename = f"report_{uuid.uuid4().hex[:6]}.json"
        
        result = dependency_audit_aggregator.aggregate_dependencies(
            repo_path=self.repo_path,
            output_report_name=report_filename,
            cve_identifier=self.cve_id,
            target_version=self.random_version
        )

        self.assertIn("report_path", result)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "SUCCESS")
        
        expected_path = os.path.join(self.repo_path, report_filename)
        self.assertEqual(result["report_path"], expected_path)
        
        self.assertTrue(os.path.exists(expected_path))
        
        with open(expected_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.assertEqual(data.get("package"), self.random_pkg)
        self.assertEqual(data.get("cve"), self.cve_id)
        self.assertEqual(data.get("target_version"), self.random_version)
        self.assertEqual(data.get("status"), "AGGREGATED")

    def test_start_new_clean_integration(self):
        branch_name = f"branch-{uuid.uuid4().hex[:6]}"
        
        result = dependency_audit_aggregator.start_new(
            repo_path=self.repo_path,
            branch=branch_name
        )
        
        self.assertIsInstance(result, dict)


if __name__ == "__main__":
    unittest.main()