import unittest
import os
import json
import uuid
import random
import tempfile
import shutil
from skills import dependency_audit_aggregator

class TestDependencyAuditAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.random_pkg = f"pkg-{uuid.uuid4().hex[:8]}"
        self.random_version = f"{random.randint(1,5)}.{random.randint(0,9)}.{random.randint(0,9)}"
        self.random_cve = f"CVE-{random.randint(2020,2024)}-{random.randint(1000,9999)}"
        self.report_filename = f"report_{uuid.uuid4().hex[:6]}.json"
        
        self.req_path = os.path.join(self.test_dir, "requirements.txt")
        with open(self.req_path, "w", encoding="utf-8") as f:
            f.write(f"# Auto-generated test requirement\n{self.random_pkg}=={self.random_version}\n")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_aggregate_dependencies_integration(self):
        result = dependency_audit_aggregator.aggregate_dependencies(
            repo_path=self.test_dir,
            output_report_name=self.report_filename,
            cve_identifier=self.random_cve,
            target_version=self.random_version
        )

        self.assertIn("report_path", result)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "SUCCESS")

        expected_file_path = os.path.join(self.test_dir, self.report_filename)
        self.assertEqual(os.path.abspath(result["report_path"]), os.path.abspath(expected_file_path))
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("package"), self.random_pkg)
        self.assertEqual(data.get("cve"), self.random_cve)
        self.assertEqual(data.get("target_version"), self.random_version)
        self.assertEqual(data.get("status"), "AGGREGATED")

    def test_start_new_integration_clean(self):
        clean_dir = tempfile.mkdtemp()
        try:
            res = dependency_audit_aggregator.start_new(repo_path=clean_dir, branch="main")
            self.assertIsInstance(res, dict)
            self.assertTrue(res.get("secure") or res.get("status") == "COMPLETED")
        finally:
            shutil.rmtree(clean_dir)

if __name__ == "__main__":
    unittest.main()