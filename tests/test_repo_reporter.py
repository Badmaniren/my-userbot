import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string

from skills.repo_reporter import RepoReporter


class TestRepoReporter(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.test_dir, uuid.uuid4().hex)
        os.makedirs(self.repo_path, exist_ok=True)
        self.reporter = RepoReporter(self.repo_path)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_init_creates_git_dir(self):
        target_repo = os.path.join(self.test_dir, uuid.uuid4().hex)
        with patch('subprocess.run') as mock_subprocess:
            reporter = RepoReporter(target_repo)
            git_dir = os.path.join(target_repo, ".git")
            self.assertTrue(os.path.exists(git_dir))

    @patch('skills.repo_reporter.RepoSummarizer')
    @patch('skills.repo_reporter.RepoAnalytics')
    def test_generate_final_report_with_get_report(self, mock_analytics_cls, mock_summarizer_cls):
        random_analytics_text = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
        random_summary_text = ''.join(random.choices(string.ascii_letters + string.digits, k=25))

        mock_analytics_inst = MagicMock()
        del mock_analytics_inst.check_status
        mock_analytics_inst.get_report.return_value = random_analytics_text
        mock_analytics_cls.return_value = mock_analytics_inst

        mock_summarizer_inst = MagicMock()
        mock_summarizer_inst.generate_summary.return_value = random_summary_text
        mock_summarizer_cls.return_value = mock_summarizer_inst

        result = self.reporter.generate_final_report()
        self.assertIn(random_analytics_text, result)
        self.assertIn(random_summary_text, result)

    @patch('skills.repo_reporter.RepoSummarizer')
    @patch('skills.repo_reporter.RepoAnalytics')
    def test_generate_final_report_with_check_status(self, mock_analytics_cls, mock_summarizer_cls):
        random_status_text = ''.join(random.choices(string.ascii_letters, k=15))
        random_summary_text = ''.join(random.choices(string.ascii_letters, k=15))

        mock_analytics_inst = MagicMock()
        if hasattr(mock_analytics_inst, 'get_report'):
            del mock_analytics_inst.get_report
        mock_analytics_inst.check_status.return_value = random_status_text
        mock_analytics_cls.return_value = mock_analytics_inst

        mock_summarizer_inst = MagicMock()
        mock_summarizer_inst.generate_summary.return_value = random_summary_text
        mock_summarizer_cls.return_value = mock_summarizer_inst

        result = self.reporter.generate_final_report()
        self.assertIn(random_status_text, result)
        self.assertIn(random_summary_text, result)

    def test_save_report_relative_path(self):
        filename = f"{uuid.uuid4().hex}.txt"
        content = uuid.uuid4().hex
        full_path = self.reporter.save_report(filename, content)

        expected_path = os.path.join(self.repo_path, filename)
        self.assertEqual(full_path, expected_path)
        self.assertTrue(os.path.exists(full_path))
        with open(full_path, 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), content)

    def test_save_report_absolute_path(self):
        abs_dir = tempfile.mkdtemp()
        try:
            filename = f"{uuid.uuid4().hex}.log"
            full_target = os.path.join(abs_dir, filename)
            content = uuid.uuid4().hex
            
            returned_path = self.reporter.save_report(full_target, content)
            self.assertEqual(returned_path, full_target)
            self.assertTrue(os.path.exists(full_target))
            with open(full_target, 'r', encoding='utf-8') as f:
                self.assertEqual(f.read(), content)
        finally:
            shutil.rmtree(abs_dir)

    @patch.object(RepoReporter, 'generate_final_report')
    @patch.object(RepoReporter, 'save_report')
    def test_generate_report_default_args(self, mock_save, mock_gen_final):
        random_final_content = uuid.uuid4().hex
        mock_gen_final.return_value = random_final_content
        expected_output_path = os.path.join(self.repo_path, "report.txt")
        mock_save.return_value = expected_output_path

        res = self.reporter.generate_report()
        mock_gen_final.assert_called_once()
        mock_save.assert_called_once_with(expected_output_path, random_final_content)
        self.assertEqual(res, expected_output_path)

    @patch.object(RepoReporter, 'generate_final_report')
    @patch.object(RepoReporter, 'save_report')
    def test_generate_report_with_status_and_summary_none_override(self, mock_save, mock_gen_final):
        random_status = uuid.uuid4().hex
        random_summary = uuid.uuid4().hex
        
        expected_content = f"{random_status}\n{random_summary}"
        custom_output = f"{uuid.uuid4().hex}.txt"
        expected_full_output = os.path.join(self.repo_path, custom_output)
        mock_save.return_value = expected_full_output

        res = self.reporter.generate_report(status=random_status, summary=random_summary, output_path=custom_output)
        mock_gen_final.assert_not_called()
        mock_save.assert_called_once_with(expected_full_output, expected_content)
        self.assertEqual(res, expected_full_output)

    @patch.object(RepoReporter, 'generate_final_report')
    @patch.object(RepoReporter, 'save_report')
    def test_generate_report_with_status_only(self, mock_save, mock_gen_final):
        random_status = uuid.uuid4().hex
        random_final = uuid.uuid4().hex
        mock_gen_final.return_value = random_final
        expected_content = f"{random_status}\n{random_final}"
        
        custom_output = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.txt")
        mock_save.return_value = custom_output

        self.reporter.generate_report(status=random_status, output_path=custom_output)
        mock_save.assert_called_once_with(custom_output, expected_content)