import os
import shutil
import unittest
import uuid
import random
from skills.repo_reporter import RepoReporter


class TestRepoReporterIntegration(unittest.TestCase):

    def setUp(self):
        self.test_id = str(uuid.uuid4())
        self.repo_path = os.path.abspath(os.path.join(".", f"test_repo_{self.test_id}"))
        if os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path)
        os.makedirs(self.repo_path, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path)

    def test_generate_and_save_report_integration(self):
        random_status = f"STATUS_OK_{uuid.uuid4()}"
        random_summary = f"SUMMARY_DATA_{uuid.uuid4()}"
        custom_report_name = f"report_{uuid.uuid4().hex[:8]}.txt"

        reporter = RepoReporter(self.repo_path)
        
        saved_file_path = reporter.generate_report(
            status=random_status,
            summary=random_summary,
            output_path=custom_report_name
        )

        self.assertTrue(os.path.exists(saved_file_path), "Отчет не был создан на диске")

        with open(saved_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(random_status, content, "Статус не найден в содержимом отчета")
        self.assertIn(random_summary, content, "Сводка не найдена в содержимом отчета")

    def test_default_pipeline_generation(self):
        reporter = RepoReporter(self.repo_path)
        
        result_path = reporter.generate_report()

        self.assertTrue(os.path.exists(result_path), "Файл отчета по умолчанию не создан")
        
        with open(result_path, "r", encoding="utf-8") as f:
            file_content = f.read()

        self.assertGreater(len(file_content), 0, "Сгенерированный отчет пуст")


if __name__ == "__main__":
    unittest.main()