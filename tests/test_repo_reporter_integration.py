import unittest
import os
import shutil
import uuid
import tempfile
from skills.repo_analytics import RepoMonitor
from skills.repo_summarizer import RepoSummarizer
from skills.repo_reporter import RepoReporter

class TestRepoReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.unique_id = str(uuid.uuid4())
        
        # Создаем фиктивный файл для аналитики
        self.test_file = os.path.join(self.repo_path, f"data_{self.unique_id}.txt")
        with open(self.test_file, "w") as f:
            f.write(f"Test content for integration: {self.unique_id}")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_reporter_integration_flow(self):
        # Инициализация компонентов
        monitor = RepoMonitor(self.repo_path)
        summarizer = RepoSummarizer(self.repo_path)
        reporter = RepoReporter(self.repo_path)

        # 1. Проверка аналитики (RepoMonitor)
        status = monitor.check_status()
        self.assertIn(self.unique_id, status, "Аналитика не обнаружила созданный файл")

        # 2. Генерация дайджеста (RepoSummarizer)
        summary = summarizer.generate_summary()
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0, "Дайджест пуст")

        # 3. Формирование отчета (RepoReporter)
        # Модуль должен использовать результаты предыдущих навыков
        report_path = reporter.generate_report(status, summary)

        # Проверка результата интеграции
        self.assertTrue(os.path.exists(report_path), "Отчет не был создан на диске")
        
        with open(report_path, "r") as f:
            content = f.read()
            self.assertIn(self.unique_id, content, "Отчет не содержит данных из аналитики")
            self.assertIn(summary, content, "Отчет не содержит данных из дайджеста")

if __name__ == "__main__":
    unittest.main()