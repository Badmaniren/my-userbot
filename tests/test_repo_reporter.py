import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.repo_reporter import RepoReporter

class TestRepoReporter(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.reporter = RepoReporter(self.repo_path)

    def test_generate_final_report_success(self):
        # Генерируем случайные данные для проверки логики
        random_summary = f"Summary: {uuid.uuid4().hex}"
        random_analytics = f"Analytics: {uuid.uuid4().hex}"
        expected_report = f"{random_analytics}\n{random_summary}"

        with patch('skills.repo_reporter.RepoSummarizer') as MockSummarizer, \
             patch('skills.repo_reporter.RepoAnalytics') as MockAnalytics:
            
            # Настройка моков
            instance_summarizer = MockSummarizer.return_value
            instance_summarizer.generate_summary.return_value = random_summary
            
            instance_analytics = MockAnalytics.return_value
            instance_analytics.get_report.return_value = random_analytics

            # Выполнение
            result = self.reporter.generate_final_report()

            # Проверка
            self.assertEqual(result, expected_report)
            instance_summarizer.generate_summary.assert_called_once()
            instance_analytics.get_report.assert_called_once()

    def test_save_report_to_file(self):
        # Генерируем случайные параметры
        file_name = f"{uuid.uuid4().hex}.txt"
        content = "".join(random.choices(string.ascii_letters, k=20))
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            self.reporter.save_report(file_name, content)
            
            # Проверка вызова записи
            mock_file.write.assert_called_once_with(content)
            mock_open.assert_called_once_with(file_name, 'w')

    def test_report_integration_flow(self):
        # Проверка цепочки вызовов: аналитика -> суммаризатор -> отчет
        random_id = uuid.uuid4().hex
        
        with patch('skills.repo_reporter.RepoSummarizer') as MockSummarizer, \
             patch('skills.repo_reporter.RepoAnalytics') as MockAnalytics:
            
            MockSummarizer.return_value.generate_summary.return_value = f"sum_{random_id}"
            MockAnalytics.return_value.get_report.return_value = f"ana_{random_id}"
            
            report = self.reporter.generate_final_report()
            
            self.assertIn(random_id, report)
            self.assertTrue(report.startswith("ana_"))
            self.assertTrue(report.endswith(f"sum_{random_id}"))

    def test_error_handling_in_analytics(self):
        # Проверка поведения при сбое в аналитике
        with patch('skills.repo_reporter.RepoAnalytics') as MockAnalytics:
            MockAnalytics.return_value.get_report.side_effect = Exception("Critical Failure")
            
            with self.assertRaises(Exception) as context:
                self.reporter.generate_final_report()
            
            self.assertEqual(str(context.exception), "Critical Failure")

if __name__ == '__main__':
    unittest.main()