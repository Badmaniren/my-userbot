import unittest
import uuid
import random
import os
import shutil
from skills.dependency_audit_validator import validate_and_aggregate_dependencies

class TestDependencyAuditValidatorIntegration(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = f"/tmp/test_repo_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        
        self.repo_path = self.test_dir
        self.branch = f"feature/audit-{uuid.uuid4().hex[:8]}"
        self.stream_source = random.choice(["npm", "pip", "maven", "go.mod"])
        self.output_report_name = f"report_{uuid.uuid4().hex}.json"
        self.cve_identifier = f"CVE-202{random.randint(0,9)}-{random.randint(1000,99999)}"
        self.target_version = f"{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,9)}"

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_validate_and_aggregate_integration(self):
        result = validate_and_aggregate_dependencies(
            repo_path=self.repo_path,
            output_report_name=self.output_report_name,
            cve_identifier=self.cve_identifier,
            target_version=self.target_version,
            branch=self.branch,
            stream_source=self.stream_source
        )

        self.assertIsNotNone(result, "Результат выполнения валидации не должен быть пустым")
        
        report_path = os.path.join(self.repo_path, self.output_report_name)
        self.assertTrue(
            os.path.exists(report_path), 
            f"Интеграционный модуль обязан создавать отчет по пути: {report_path}"
        )
        
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.cve_identifier, content, "Отчет должен содержать переданный CVE идентификатор")
            self.assertIn(self.target_version, content, "Отчет должен содержать целевую версию зависимости")

if __name__ == "__main__":
    unittest.main()