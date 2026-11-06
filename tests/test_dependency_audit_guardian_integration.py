import unittest
import uuid
import random
import os
from skills import dependency_audit_guardian

class TestDependencyAuditGuardianIntegration(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/test_repo_{uuid.uuid4()}"
        os.makedirs(self.repo_path, exist_ok=True)
        self.branch = f"feature-{uuid.uuid4().hex[:8]}"
        self.stream = f"stream-{random.randint(1000, 9999)}"
        self.report_name = f"report_{uuid.uuid4().hex[:6]}.json"
        self.cve_id = f"CVE-2023-{random.randint(10000, 99999)}"
        self.target_version = f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.chaos_data = os.urandom(random.randint(16, 64))

    def tearDown(self):
        if os.path.exists(self.repo_path):
            try:
                os.rmdir(self.repo_path)
            except OSError:
                pass

    def test_start_new_audit_integration(self):
        result = dependency_audit_guardian.start_new_audit(
            self.repo_path, self.branch, self.stream
        )
        self.assertIsNotNone(result)

    def test_execute_guarded_audit_integration(self):
        result = dependency_audit_guardian.execute_guarded_audit(
            self.repo_path, self.report_name, self.cve_id, self.target_version, self.branch, self.stream
        )
        self.assertIsNotNone(result)

    def test_apply_audit_data_integration(self):
        result = dependency_audit_guardian.apply_audit_data(self.chaos_data)
        self.assertIsNotNone(result)

    def test_validate_and_aggregate_dependencies_integration(self):
        result = dependency_audit_guardian.validate_and_aggregate_dependencies(
            self.repo_path, self.report_name, self.cve_id, self.target_version, self.branch, self.stream
        )
        self.assertIsNotNone(result)

if __name__ == "__main__":
    unittest.main()