import os
import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
from skills.repo_reporter import RepoReporter


class TestRepoReporter(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"

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

    def test_init_creates_git_repository(self):
        non_existent_path = os.path.join(self.repo_path, uuid.uuid4().hex)
        with patch('subprocess.run') as mock_run:
            reporter = RepoReporter(non_existent_path)
            self.assertTrue(os.path.exists(non_existent_path))
            self.assertTrue(os.path.exists(os.path.join(non_existent_path, ".git")))
            mock_run.assert_called_once()

    def test_generate_final_report_success(self):
        random_analytics = uuid.uuid4().hex
        random_summary = uuid.uuid4().hex

        with patch('skills.repo_reporter.RepoAnalytics') as mock_analytics_class, \
             patch('skills.repo_reporter.RepoSummarizer') as mock_summarizer_class:
            
            mock_analytics_instance = MagicMock()
            mock_analytics_instance.get_report.return_value = random_analytics
            mock_analytics_class.return_value = mock_analytics_instance

            mock_summarizer_instance = MagicMock()
            mock_summarizer_instance.generate_summary.return_value = random_summary
            mock_summarizer_class.return_value = mock_summarizer_instance

            reporter = RepoReporter(self.repo_path)
            report = reporter.generate_final_report()

            self.assertIn(random_analytics, report)
            self.assertIn(random_summary, report)

    def test_save_report_to_file(self):
        random_filename = f"{uuid.uuid4().hex}.txt"
        random_content = uuid.uuid4().hex

        reporter = RepoReporter(self.repo_path)
        full_path = reporter.save_report(random_filename, random_content)

        self.assertTrue(os.path.exists(full_path))
        with open(full_path, 'r') as f:
            content = f.read()
        self.assertEqual(content, random_content)

        if os.path.exists(random_filename):
            try:
                os.remove(random_filename)
            except OSError:
                pass

    def test_save_report_nested_directory(self):
        nested_dir = uuid.uuid4().hex
        random_filename = f"{uuid.uuid4().hex}.log"
        random_content = uuid.uuid4().hex
        relative_path = os.path.join(nested_dir, random_filename)

        reporter = RepoReporter(self.repo_path)
        full_path = reporter.save_report(relative_path, random_content)

        expected_path = os.path.join(self.repo_path, relative_path)
        self.assertEqual(full_path, expected_path)
        self.assertTrue(os.path.exists(expected_path))
        
        with open(expected_path, 'r') as f:
            content = f.read()
        self.assertEqual(content, random_content)

    def test_generate_report_custom_params(self):
        random_status = uuid.uuid4().hex
        random_summary = uuid.uuid4().hex
        random_output = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.txt")

        reporter = RepoReporter(self.repo_path)
        result_path = reporter.generate_report(status=random_status, summary=random_summary, output_path=random_output)

        self.assertEqual(result_path, random_output)
        self.assertTrue(os.path.exists(random_output))

        with open(random_output, 'r') as f:
            content = f.read()

        self.assertIn(random_status, content)
        self.assertIn(random_summary, content)

    def test_generate_report_default_params(self):
        random_analytics = uuid.uuid4().hex
        random_summary = uuid.uuid4().hex

        with patch('skills.repo_reporter.RepoAnalytics') as mock_analytics_class, \
             patch('skills.repo_reporter.RepoSummarizer') as mock_summarizer_class:
            
            mock_analytics_instance = MagicMock()
            if hasattr(mock_analytics_instance, 'get_report'):
                mock_analytics_instance.get_report.return_value = random_analytics
            mock_analytics_class.return_value = mock_analytics_instance

            mock_summarizer_instance = MagicMock()
            mock_summarizer_instance.generate_summary.return_value = random_summary
            mock_summarizer_class.return_value = mock_summarizer_instance

            reporter = RepoReporter(self.repo_path)
            result_path = reporter.generate_report()

            expected_default_path = os.path.join(self.repo_path, "report.txt")
            self.assertEqual(result_path, expected_default_path)
            self.assertTrue(os.path.exists(expected_default_path))

            with open(expected_default_path, 'r') as f:
                content = f.read()

            self.assertIn(random_analytics, content)
            self.assertIn(random_summary, content)


if __name__ == '__main__':
    unittest.main()