import unittest
from unittest.mock import patch
import os
import shutil
import uuid
import random
from skills.repo_reporter import RepoReporter


class TestRepoReporter(unittest.TestCase):
    def setUp(self):
        self.rand_prefix = uuid.uuid4().hex[:8]
        self.repo_path = os.path.join(os.getcwd(), f"test_repo_{self.rand_prefix}")
        os.makedirs(self.repo_path, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path, ignore_errors=True)

    def test_init_creates_git_dir(self):
        custom_repo = os.path.join(os.getcwd(), f"custom_repo_{uuid.uuid4().hex[:8]}")
        try:
            reporter = RepoReporter(custom_repo)
            git_path = os.path.join(custom_repo, ".git")
            self.assertTrue(os.path.exists(git_path))
        finally:
            if os.path.exists(custom_repo):
                shutil.rmtree(custom_repo, ignore_errors=True)

    @patch('skills.repo_reporter.RepoAnalytics')
    @patch('skills.repo_reporter.RepoSummarizer')
    def test_generate_final_report_success(self, mock_summarizer_cls, mock_analytics_cls):
        rand_analytics_msg = f"analytics_{uuid.uuid4().hex}"
        rand_summary_msg = f"summary_{uuid.uuid4().hex}"

        mock_analytics_inst = mock_analytics_cls.return_value
        mock_analytics_inst.get_report.return_value = rand_analytics_msg

        mock_summarizer_inst = mock_summarizer_cls.return_value
        mock_summarizer_inst.generate_summary.return_value = rand_summary_msg

        reporter = RepoReporter(self.repo_path)
        report = reporter.generate_final_report()

        self.assertIn(rand_analytics_msg, report)
        self.assertIn(rand_summary_msg, report)

    def test_save_report_relative_path(self):
        rand_filename = f"report_{uuid.uuid4().hex[:6]}.txt"
        rand_content = f"content_{uuid.uuid4().hex}"

        reporter = RepoReporter(self.repo_path)
        saved_path = reporter.save_report(rand_filename, rand_content)

        expected_path = os.path.join(self.repo_path, rand_filename)
        self.assertEqual(os.path.abspath(saved_path), os.path.abspath(expected_path))
        self.assertTrue(os.path.exists(expected_path))

        with open(expected_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, rand_content)

    def test_save_report_absolute_path(self):
        rand_filename = f"abs_report_{uuid.uuid4().hex[:6]}.txt"
        abs_file_path = os.path.join(self.repo_path, rand_filename)
        rand_content = f"content_{uuid.uuid4().hex}"

        reporter = RepoReporter(self.repo_path)
        saved_path = reporter.save_report(abs_file_path, rand_content)

        self.assertEqual(os.path.abspath(saved_path), os.path.abspath(abs_file_path))
        self.assertTrue(os.path.exists(abs_file_path))

        with open(abs_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, rand_content)

    @patch('skills.repo_reporter.RepoReporter.generate_final_report')
    def test_generate_report_default_params(self, mock_gen_final):
        rand_final_content = f"final_{uuid.uuid4().hex}"
        mock_gen_final.return_value = rand_final_content

        reporter = RepoReporter(self.repo_path)
        output_file = f"out_{uuid.uuid4().hex[:6]}.txt"
        
        result_path = reporter.generate_report(output_path=output_file)

        self.assertTrue(os.path.exists(result_path))
        with open(result_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, rand_final_content)

    @patch('skills.repo_reporter.RepoReporter.generate_final_report')
    def test_generate_report_with_status_and_summary(self, mock_gen_final):
        rand_status = f"status_{uuid.uuid4().hex}"
        rand_summary = f"summary_{uuid.uuid4().hex}"
        rand_output = f"custom_out_{uuid.uuid4().hex[:6]}.txt"

        reporter = RepoReporter(self.repo_path)
        result_path = reporter.generate_report(status=rand_status, summary=rand_summary, output_path=rand_output)

        mock_gen_final.assert_not_called()

        with open(result_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn(rand_status, content)
        self.assertIn(rand_summary, content)