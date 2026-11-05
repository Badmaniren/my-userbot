import unittest
import os
import shutil
import uuid
import random
from skills.dependency_audit_exporter import export_dependency_audit
from skills.dependency_audit_aggregator import aggregate_dependencies
from skills.dependency_audit_reporter import DependencyAuditReporter

class TestDependencyAuditExporterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.abspath(f"./test_repo_{uuid.uuid4().hex}")
        os.makedirs(self.test_dir, exist_ok=True)

        self.branch = f"branch-{uuid.uuid4().hex[:8]}"
        self.stream_source = f"stream-{uuid.uuid4().hex[:8]}"
        self.output_report_name = f"audit_report_{uuid.uuid4().hex[:6]}.json"
        self.cve_identifier = f"CVE-2023-{random.randint(1000, 9999)}"
        self.target_version = f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}"

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

        report_path = os.path.join(self.test_dir, self.output_report_name)
        if os.path.exists(report_path):
            os.remove(report_path)

    def test_export_dependency_audit_integration(self):
        result = export_dependency_audit(
            repo_path=self.test_dir,
            branch=self.branch,
            stream_source=self.stream_source,
            output_report_name=self.output_report_name,
            cve_identifier=self.cve_identifier,
            target_version=self.target_version
        )

        self.assertIsNotNone(result, "Экспортер должен возвращать результат выполнения")

        expected_file_path = os.path.join(self.test_dir, self.output_report_name)
        self.assertTrue(
            os.path.exists(expected_file_path),
            f"Интеграционный вызов должен реально создать файл отчета по пути: {expected_file_path}"
        )

        with open(expected_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertGreater(len(content), 0, "Файл отчета не должен быть пустым")
            self.assertIn(self.cve_identifier, content, "Отчет должен содержать переданный CVE идентификатор")
            self.assertIn(self.target_version, content, "Отчет должен содержать целевую версию")

if __name__ == "__main__":
    unittest.main()