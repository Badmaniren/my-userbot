import unittest
import os
import json
import uuid
import random
import tempfile
import shutil
from skills import dependency_audit_aggregator
from skills import vulnerability_analyzer
from skills import dependency_updater_pipeline
from skills import repo_reporter

class TestDependencyAuditAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.random_pkg = f"pkg-{uuid.uuid4().hex[:8]}"
        self.random_version = f"{random.randint(1,9)}.{random.randint(0,9)}.{random.randint(0,9)}"
        self.cve_id = f"CVE-2023-{random.randint(10000,99999)}"
        
        self.req_path = os.path.join(self.test_dir, "requirements.txt")
        with open(self.req_path, "w", encoding="utf-8") as f:
            f.write(f"{self.random_pkg}=={self.random_version}\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_start_new_integration_clean(self):
        empty_dir = tempfile.mkdtemp()
        try:
            result = dependency_audit_aggregator.start_new(repo_path=empty_dir)
            self.assertIn("secure", result)
            self.assertTrue(result["secure"])
        finally:
            shutil.rmtree(empty_dir, ignore_errors=True)

    def test_aggregate_dependencies_real_io(self):
        report_name = f"report_{uuid.uuid4().hex[:6]}.json"
        
        result = dependency_audit_aggregator.aggregate_dependencies(
            repo_path=self.test_dir,
            output_report_name=report_name,
            cve_identifier=self.cve_id,
            target_version="2.0.0"
        )

        self.assertEqual(result["status"], "SUCCESS")
        expected_path = os.path.join(self.test_dir, report_name)
        self.assertEqual(result["report_path"], expected_path)
        
        self.assertTrue(os.path.exists(expected_path))
        
        with open(expected_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.assertEqual(data["package"], self.random_pkg)
        self.assertEqual(data["cve"], self.cve_id)
        self.assertEqual(data["target_version"], "2.0.0")
        self.assertEqual(data["status"], "AGGREGATED")

if __name__ == "__main__":
    unittest.main()