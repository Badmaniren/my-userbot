import os
import shutil
import unittest
import uuid
import random
from skills.repo_reporter import RepoReporter


class TestRepoReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.test_dir = os.path.abspath(os.path.join(".", f"test_repo_{self.random_suffix}"))
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_generate_and_save_report_integration(self):
        reporter = RepoReporter(self.test_dir)
        
        random_status = f"STATUS_ID_{uuid.uuid4().hex[:6]}"
        random_summary = f"SUMMARY_DATA_{random.randint(1000, 9999)}"
        custom_report_name = f"report_{uuid.uuid4().hex[:6]}.txt"
        
        saved_path = reporter.generate_report(
            status=random_status,
            summary=random_summary,
            output_path=custom_report_name
        )
        
        self.assertTrue(os.path.exists(saved_path), "Отчет не был создан в файловой системе")
        
        with open(saved_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        self.assertIn(random_status, content, "Случайный статус не найден в содержимом отчета")
        self.assertIn(random_summary, content, "Случайная сводка не найдена в содержимом отчета")

    def test_default_pipeline_report_integration(self):
        reporter = RepoReporter(self.test_dir)
        
        saved_path = reporter.generate_report()
        
        self.assertTrue(os.path.exists(saved_path), "Отчет по умолчанию не был создан")
        
        default_file_name = "report.txt"
        expected_full_path = os.path.join(self.test_dir, default_file_name)
        self.assertEqual(saved_path, expected_full_path)
        
        with open(saved_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        self.assertGreater(len(content), 0, "Сгенерированный файл отчета оказался пустым")


if __name__ == "__main__":
    unittest.main()