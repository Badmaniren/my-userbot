import unittest
from unittest.mock import patch, MagicMock
import os
import shutil
import uuid
import random
import string
from skills.repo_reporter import RepoReporter


class TestRepoReporter(unittest.TestCase):
    def setUp(self):
        self.random_prefix = uuid.uuid4().hex[:8]
        self.test_repo_path = os.path.abspath(f"test_repo_{self.random_prefix}")
        if not os.path.exists(self.test_repo_path):
            os.makedirs(self.test_repo_path)

    def tearDown(self):
        if os.path.exists(self.test_repo_path):
            shutil.rmtree(self.test_repo_path, ignore_errors=True)

    def test_init_creates_git_dir(self):
        sub_dir = os.path.join(self.test_repo_path, uuid.uuid4().hex)
        reporter = RepoReporter(sub_dir)
        git_dir = os.path.join(sub_dir, ".git")
        self.assertTrue(os.path.exists(git_dir))
        shutil.rmtree(sub_dir, ignore_errors=True)

    @patch('skills.repo_reporter.RepoAnalytics')
    @patch('skills.repo_reporter.RepoSummarizer')
    def test_generate_final_report_analytics_get_report(self, mock_summarizer_cls, mock_analytics_cls):
        random_analytics_msg = f"analytics_{uuid.uuid4().hex}"
        random_summary_msg = f"summary_{uuid.uuid4().hex}"

        mock_analytics_instance = MagicMock()
        del mock_analytics_instance.check_status
        mock_analytics_instance.get_report.return_value = random_analytics_msg
        mock_analytics_cls.return_value = mock_analytics_instance

        mock_summarizer_instance = MagicMock()
        mock_summarizer_instance.generate_summary.return_value = random_summary_msg
        mock_summarizer_cls.return_value = mock_summarizer_instance

        reporter = RepoReporter(self.test_repo_path)
        result = reporter.generate_final_report()

        expected = f"{random_analytics_msg}\n{random_summary_msg}"
        self.assertEqual(result, expected)
        mock_analytics_instance.get_report.assert_called_once()
        mock_summarizer_instance.generate_summary.assert_called_once()

    @patch('skills.repo_reporter.RepoAnalytics')
    @patch('skills.repo_reporter.RepoSummarizer')
    def test_generate_final_report_analytics_check_status(self, mock_summarizer_cls, mock_analytics_cls):
        random_status_msg = f"status_{uuid.uuid4().hex}"
        random_summary_msg = f"summary_{uuid.uuid4().hex}"

        mock_analytics_instance = MagicMock()
        del mock_analytics_instance.get_report
        mock_analytics_instance.check_status.return_value = random_status_msg
        mock_analytics_cls.return_value = mock_analytics_instance

        mock_summarizer_instance = MagicMock()
        mock_summarizer_instance.generate_summary.return_value = random_summary_msg
        mock_summarizer_cls.return_value = mock_summarizer_instance

        reporter = RepoReporter(self.test_repo_path)
        result = reporter.generate_final_report()

        expected = f"{random_status_msg}\n{random_summary_msg}"
        self.assertEqual(result, expected)
        mock_analytics_instance.check_status.assert_called_once()

    def test_save_report_relative_path(self):
        reporter = RepoReporter(self.test_repo_path)
        filename = f"{uuid.uuid4().hex}.txt"
        content = ''.join(random.choices(string.ascii_letters + string.digits, k=30))

        full_path = reporter.save_report(filename, content)
        expected_path = os.path.join(self.test_repo_path, filename)
        self.assertEqual(full_path, expected_path)
        self.assertTrue(os.path.exists(expected_path))

        with open(expected_path, 'r', encoding='utf-8') as f:
            read_content = f.read()
        self.assertEqual(read_content, content)

    def test_save_report_absolute_path(self):
        reporter = RepoReporter(self.test_repo_path)
        abs_dir = os.path.join(self.test_repo_path, uuid.uuid4().hex)
        filename = f"{uuid.uuid4().hex}.log"
        abs_filepath = os.path.join(abs_dir, filename)
        content = uuid.uuid4().hex

        full_path = reporter.save_report(abs_filepath, content)
        self.assertEqual(full_path, abs_filepath)
        self.assertTrue(os.path.exists(abs_filepath))

        with open(abs_filepath, 'r', encoding='utf-8') as f:
            read_content = f.read()
        self.assertEqual(read_content, content)

    @patch.object(RepoReporter, 'generate_final_report')
    @patch.object(RepoReporter, 'save_report')
    def test_generate_report_defaults(self, mock_save_report, mock_gen_final):
        random_final_content = uuid.uuid4().hex
        mock_gen_final.return_value = random_final_content
        random_saved_path = f"/fake/path/{uuid.uuid4().hex}"
        mock_save_report.return_value = random_saved_path

        reporter = RepoReporter(self.test_repo_path)
        res = reporter.generate_report()

        mock_gen_final.assert_called_once()
        expected_default_output = os.path.join(self.test_repo_path, "report.txt")
        mock_save_report.assert_called_once_with(expected_default_output, random_final_content)
        self.assertEqual(res, random_saved_path)

    @patch.object(RepoReporter, 'save_report')
    def test_generate_report_with_status_and_summary(self, mock_save_report):
        random_status = uuid.uuid4().hex
        random_summary = uuid.uuid4().hex
        random_output = f"{uuid.uuid4().hex}.txt"

        reporter = RepoReporter(self.test_repo_path)
        reporter.generate_report(status=random_status, summary=random_summary, output_path=random_output)

        expected_content = f"{random_status}\n{random_summary}"
        expected_path = os.path.join(self.test_repo_path, random_output)
        mock_save_report.assert_called_once_with(expected_path, expected_content)


if __name__ == '__main__':
    unittest.main()