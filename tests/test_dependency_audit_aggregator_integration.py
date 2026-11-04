import unittest
import uuid
import random
import os
import tempfile
import shutil
from skills.dependency_audit_aggregator import aggregate_dependencies

class TestDependencyAuditAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.test_dir, f"repo_{uuid.uuid4().hex}")
        os.makedirs(self.repo_path)
        
        self.random_pkg_name = f"pkg-{uuid.uuid4().hex[:8]}"
        self.random_old_version = f"1.{random.randint(0, 5)}.{random.randint(0, 9)}"
        self.random_new_version = f"2.{random.randint(0, 5)}.{random.randint(0, 9)}"
        self.random_cve_id = f"CVE-2023-{random.randint(10000, 99999)}"
        
        req_file = os.path.join(self.repo_path, "requirements.txt")
        with open(req_file, "w") as f:
            f.write(f"{self.random_pkg_name}=={self.random_old_version}\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_aggregate_dependencies_integration(self):
        output_filename = f"audit_report_{uuid.uuid4().hex}.json"
        
        result = aggregate_dependencies(
            repo_path=self.repo_path,
            output_report_name=output_filename,
            cve_identifier=self.random_cve_id,
            target_version=self.random_new_version
        )

        self.assertIsInstance(result, dict, "Результат должен быть словарем")
        self.assertIn("report_path", result, "В результате должен быть путь к отчету")
        
        expected_file_path = result["report_path"]
        self.assertTrue(os.path.exists(expected_file_path), "Файл отчета должен реально существовать на диске")
        
        with open(expected_file_path, "r", encoding="utf-8") as f:
            report_content = f.read()
            self.assertIn(self.random_pkg_name, report_content, "Отчет должен содержать имя зависимого пакета")
            self.assertIn(self.random_cve_id, report_content, "Отчет должен содержать сгенерированный CVE ID")
            self.assertIn(self.random_new_version, report_content, "Отчет должен содержать целевую версию обновления")

if __name__ == "__main__":
    unittest.main()