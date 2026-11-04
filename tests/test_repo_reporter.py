import os
import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import tempfile
import shutil

from skills.repo_reporter import RepoReporter


class TestRepoReporter(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.rand_repo_name = uuid.uuid4().hex
        self.repo_path = os.path.join(self.test_dir, self.rand_repo_name)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_init_creates_git_repository(self):
        non_existent_path = os.path.join(self.repo_path, uuid.uuid4().hex, uuid.uuid4().hex)
        self.assertFalse(os.path.exists(non_existent_path))
        
        with patch("subprocess.run") as mock_run:
            reporter = RepoReporter(non_existent_path)
            self.assertTrue(os.path.exists(non_existent_path))
            git_dir = os.path.join(non_existent_path, ".git")
            self.assertTrue(os.path.exists(git_dir))
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertIn("git", args)
            self.assertIn("init", args)

    def test_generate_final_report_success(self):
        rand_analytics = uuid.uuid4().hex
        rand_summary = uuid.uuid4().hex

        with patch("skills.repo_reporter.RepoAnalytics") as mock_analytics_cls, \
             patch("skills.repo_reporter.RepoSummarizer") as mock_summarizer_cls:
            
            mock_analytics_instance = mock_analytics_cls.return_value
            mock_analytics_instance.get_report.return_value = rand_analytics
            
            mock_summarizer_instance = mock_summarizer_cls.return_value
            mock_summarizer_instance.generate_summary.return_value = rand_summary

            reporter = RepoReporter(self.repo_path)
            result = reporter.generate_final_report()

            self.assertIn(rand_analytics, result)
            self.assertIn(rand_summary, result)
            mock_analytics_instance.get_report.assert_called_once()
            mock_summarizer_instance.generate_summary.assert_called_once()

    def test_generate_final_report_fallback_check_status(self):
        rand_status = uuid.uuid4().hex
        rand_summary = uuid.uuid4().hex

        with patch("skills.repo_reporter.RepoAnalytics") as mock_analytics_cls, \
             patch("skills.repo_reporter.RepoSummarizer") as mock_summarizer_cls:
            
            mock_analytics_instance = mock_analytics_cls.return_value
            del mock_analytics_instance.get_report
            mock_analytics_instance.check_status.return_value = rand_status
            
            mock_summarizer_instance = mock_summarizer_cls.return_value
            mock_summarizer_instance.generate_summary.return_value = rand_summary

            reporter = RepoReporter(self.repo_path)
            result = reporter.generate_final_report()

            self.assertIn(rand_status, result)
            self.assertIn(rand_summary, result)
            mock_analytics_instance.check_status.assert_called_once()

    def test_save_report_relative_path(self):
        rand_filename = f"{uuid.uuid4().hex}.txt"
        rand_content = uuid.uuid4().hex

        reporter = RepoReporter(self.repo_path)
        full_path = reporter.save_report(rand_filename, rand_content)

        expected_path = os.path.join(self.repo_path, rand_filename)
        self.assertEqual(full_path, expected_path)
        self.assertTrue(os.path.exists(full_path))

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, rand_content)

    def test_save_report_absolute_path(self):
        rand_filename = f"{uuid.uuid4().hex}.log"
        rand_content = uuid.uuid4().hex
        abs_file_path = os.path.join(self.test_dir, uuid.uuid4().hex, rand_filename)

        reporter = RepoReporter(self.repo_path)
        full_path = reporter.save_report(abs_file_path, rand_content)

        self.assertEqual(full_path, abs_file_path)
        self.assertTrue(os.path.exists(abs_file_path))

        with open(abs_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, rand_content)

    def test_generate_report_defaults(self):
        rand_final = uuid.uuid4().hex
        rand_output = f"{uuid.uuid4().hex}.txt"

        with patch.object(RepoReporter, "generate_final_report", return_value=rand_final) as mock_gen_final, \
             patch.object(RepoReporter, "save_report") as mock_save:
            
            reporter = RepoReporter(self.repo_path)
            reporter.generate_report(output_path=rand_output)

            mock_gen_final.assert_called_once()
            mock_save.assert_called_once()
            saved_path, saved_content = mock_save.call_args[0]
            self.assertEqual(saved_content, rand_final)
            self.assertTrue(saved_path.endswith(rand_output))

    def test_generate_report_custom_status_and_summary(self):
        rand_status = uuid.uuid4().hex
        rand_summary = uuid.uuid4().hex
        rand_output = uuid.uuid4().hex

        with patch.object(RepoReporter, "save_report", return_value=uuid.uuid4().hex) as mock_save:
            reporter = RepoReporter(self.repo_path)
            reporter.generate_report(status=rand_status, summary=rand_summary, output_path=rand_output)

            mock_save.assert_called_once()
            _, saved_content = mock_save.call_args[0]
            self.assertIn(rand_status, saved_content)
            self.assertIn(rand_summary, saved_content)