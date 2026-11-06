import unittest
import uuid
import random
import os
import tempfile
import shutil
from skills.repo_health_analyzer import repo_health_analyzer
from skills.dependency_scanner import dependency_scanner
from skills.vulnerability_analyzer import vulnerability_analyzer
from skills.repo_auditor import repo_auditor
from skills.repo_reporter import repo_reporter

class TestRepoHealthAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.unique_id = str(uuid.uuid4())
        self.random_version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        
        self.req_file = os.path.join(self.test_dir, "requirements.txt")
        with open(self.req_file, "w") as f:
            f.write(f"vulnerable-package=={self.random_version}\n")

    def tearDownno_mock(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_repo_health_analyzer_real_pipeline(self):
        scan_result = dependency_scanner(self.test_dir)
        vuln_result = vulnerability_analyzer(scan_result)
        audit_result = repo_auditor(self.test_dir)
        
        analysis_context = {
            "run_id": self.unique_id,
            "target_path": self.test_dir,
            "scan_data": scan_result,
            "vulnerabilities": vuln_result,
            "audit": audit_result
        }

        health_report = repo_health_analyzer(analysis_context)
        
        self.assertIsInstance(health_report, dict)
        self.assertIn("status", health_report)
        
        report_output = repo_reporter(health_report)
        self.assertIsNotNone(report_output)

        report_file_path = os.path.join(self.test_dir, f"health_report_{self.unique_id}.json")
        with open(report_file_path, "w") as f:
            f.write(str(health_report))

        self.assertTrue(os.path.exists(report_file_path), "Файл отчета о здоровье репозитория должен быть реально создан на диске.")
        
        with open(report_file_path, "r") as f:
            content = f.read()
            self.assertIn(self.unique_id, content, "Случайный UUID должен присутствовать в артефактах выполнения.")

if __name__ == "__main__":
    unittest.main()