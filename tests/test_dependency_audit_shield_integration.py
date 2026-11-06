import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.dependency_audit_shield import run_dependency_audit_shield

class TestDependencyAuditShieldIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.output_report_name = f"audit_report_{uuid.uuid4().hex}.json"
        self.cve_identifier = f"CVE-{random.randint(2000, 2024)}-{random.randint(1000, 9999)}"
        self.target_version = f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.branch = f"feature/fix-{uuid.uuid4().hex[:8]}"
        self.stream_source = f"stream-{uuid.uuid4().hex[:6]}"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_dependency_audit_shield_integration(self):
        result = run_dependency_audit_shield(
            repo_path=self.repo_path,
            output_report_name=self.output_report_name,
            cve_identifier=self.cve_identifier,
            target_version=self.target_version,
            branch=self.branch,
            stream_source=self.stream_source
        )

        self.assertIsNotNone(result, "Модуль dependency_audit_shield должен возвращать результат.")

        report_path = os.path.join(self.repo_path, self.output_report_name)
        self.assertTrue(
            os.path.exists(report_path),
            f"Интеграционный процесс должен создавать отчет по пути: {report_path}"
        )

if __name__ == "__main__":
    unittest.main()