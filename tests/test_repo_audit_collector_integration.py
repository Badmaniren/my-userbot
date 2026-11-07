import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_audit_collector import RepoAuditCollector

class TestRepoAuditCollectorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()

        self.unique_id = str(uuid.uuid4())
        self.random_metric_value = random.randint(100, 999)

        self.dummy_file_name = f"test_file_{self.unique_id}.py"
        self.dummy_file_path = os.path.join(self.test_dir, self.dummy_file_name)

        with open(self.dummy_file_path, "w", encoding="utf-8") as f:
            f.write(f"# Unique test token: {self.unique_id}\n")
            f.write(f"METRIC_SEED = {self.random_metric_value}\n")
            f.write("def compute_sum(a, b):\n    return a + b\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_collect_and_aggregate_integration(self):
        collector = RepoAuditCollector(
            repository_path=self.test_dir,
            output_dir=self.output_dir
        )

        result = collector.collect_and_aggregate()

        self.assertIsInstance(result, dict)
        self.assertIn("metrics", result)
        self.assertIn("issues", result)
        self.assertIn("structure", result)
        self.assertIn("synthesis", result)
        self.assertIn("export_path", result)

        export_path = result["export_path"]
        if export_path:
            self.assertTrue(
                os.path.exists(export_path),
                f"Экспортированный отчет не найден по пути: {export_path}"
            )

    def test_export_aggregated_report_integration(self):
        collector = RepoAuditCollector(
            repository_path=self.test_dir,
            output_dir=self.output_dir
        )

        custom_filename = f"audit_report_{self.unique_id}.json"
        export_path = collector.export_aggregated_report(filename=custom_filename)

        self.assertIsNotNone(export_path)
        self.assertTrue(
            os.path.exists(export_path),
            f"Файл отчета не был создан: {export_path}"
        )

        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertTrue(len(content) > 0, "Файл отчета пуст")

if __name__ == "__main__":
    unittest.main()