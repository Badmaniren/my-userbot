import unittest
import os
import shutil
import uuid
import random
from skills.dependency_audit_pipeline import run_dependency_audit_pipeline

class TestDependencyAuditPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = f"/tmp/test_repo_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        
        self.repo = self.test_dir
        self.branch = f"feature/audit-{uuid.uuid4().hex[:8]}"
        self.stream = f"stream-{random.randint(1000, 9999)}"
        self.cve = f"CVE-202{random.randint(0,9)}-{random.randint(1000, 9999)}"
        self.version = f"1.{random.randint(0,5)}.{random.randint(0,20)}"
        self.output_report = f"report_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        report_path = os.path.join(self.repo, self.output_report)
        if os.path.exists(report_path):
            os.remove(report_path)

    def test_dependency_audit_pipeline_end_to_end(self):
        result = run_dependency_audit_pipeline(
            repo_path=self.repo,
            branch=self.branch,
            stream_source=self.stream,
            cve_identifier=self.cve,
            target_version=self.version,
            output_report_name=self.output_report
        )

        self.assertIsNotNone(result, "Пайплайн не должен возвращать None")
        
        report_path = os.path.join(self.repo, self.output_report)
        self.assertTrue(
            os.path.exists(report_path), 
            f"Отчет должен быть физически создан модулем reporter по пути {report_path}"
        )

        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.cve, content, "Сгенерированный отчет должен содержать переданный CVE идентификатор")
            self.assertIn(self.version, content, "Сгенерированный отчет должен содержать целевую версию")

if __name__ == "__main__":
    unittest.main()