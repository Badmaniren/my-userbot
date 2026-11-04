import os
import unittest
import uuid
import random
from skills.repo_reporter import RepoReporter
from skills.repo_analytics import RepoMonitor as RepoAnalytics
from skills.repo_summarizer import RepoSummarizer


class TestRepoReporterIntegration(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.repo_path = os.path.join(os.getcwd(), f"test_repo_{self.random_suffix}")
        os.makedirs(self.repo_path, exist_ok=True)
        
        self.reporter = RepoReporter(self.repo_path)

    def tearDown(self):
        if os.path.exists(self.repo_path):
            for root, dirs, files in os.walk(self.repo_path, topdown=False):
                for name in files:
                    try:
                        os.remove(os.path.join(root, name))
                    except OSError:
                        pass
                for name in dirs:
                    try:
                        os.rmdir(os.path.join(root, name))
                    except OSError:
                        pass
            try:
                os.rmdir(self.repo_path)
            except OSError:
                pass

    def test_generate_and_save_complex_report_integration(self):
        unique_status = f"SECURITY_STATUS_{uuid.uuid4().hex[:6]}: OK"
        unique_summary = f"SUMMARY_ID_{random.randint(1000, 9999)}: All systems nominal"
        custom_filename = f"report_{uuid.uuid4().hex[:6]}.txt"

        saved_path = self.reporter.generate_report(
            status=unique_status,
            summary=unique_summary,
            output_path=custom_filename
        )

        self.assertTrue(os.path.exists(saved_path), "Файл отчета не был создан в файловой системе")

        with open(saved_path, 'r', encoding='utf-8') as f:
            file_content = f.read()

        self.assertIn(unique_status, file_content, "Статус безопасности не найден в сохраненном отчете")
        self.assertIn(unique_summary, file_content, "Сводка не найдена в сохраненном отчете")

    def test_fully_automatic_report_generation_integration(self):
        dummy_file_name = f"source_{uuid.uuid4().hex[:4]}.py"
        dummy_file_path = os.path.join(self.repo_path, dummy_file_name)
        
        random_code_marker = f"SECRET_TOKEN = '{uuid.uuid4().hex}'"
        with open(dummy_file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Test code\n{random_code_marker}\n")

        final_report = self.reporter.generate_final_report()
        
        self.assertIsInstance(final_report, str, "Отчет должен быть строкового типа")
        self.assertTrue(len(final_report) > 0, "Сгенерированный итоговый отчет не должен быть пустым")

        default_output = self.reporter.generate_report()
        self.assertTrue(os.path.exists(default_output), "Отчет по умолчанию не создан")

        with open(default_output, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertTrue(len(content) > 0, "Файл отчета по умолчанию пуст")


if __name__ == '__main__':
    unittest.main()