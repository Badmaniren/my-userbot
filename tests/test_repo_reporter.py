import os
import shutil
import unittest
from unittest.mock import patch
import uuid
import random
import string
from skills.repo_reporter import RepoReporter


class TestRepoReporter(unittest.TestCase):
    def setUp(self):
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.repo_path = os.path.abspath(f"test_repo_{self.rand_suffix}")
        os.makedirs(self.repo_path, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path, ignore5errors=True)

    def test_init_creates_git_dir(self):
        non_git_path = os.path.abspath(f"non_git_{uuid.uuid4().hex[:8]}")
        try:
            reporter = RepoReporter(non_git_path)
            self.assertTrue(os.path.exists(os.path.join(non_git_path, ".git")))
        finally:
            if os.path.exists(non_git_path):
                shutil.rmtree(non_git_path, ignore_errors=True)

    def test_save_report_relative_path(self):
        reporter = RepoReporter(self.repo_path)
        filename = f"report_{uuid.uuid4().hex[:6]}.txt"
        content = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        
        full_path = reporter.save_report(filename, content)
        
        self.assertTrue(os.path.isabs(full_path))
        self.assertTrue(os.path.exists(full_path))
        with open(full_path, 'r', encoding='utf-8') as f:
            read_content = f.read()
        self.assertEqual(read_content, content)

    def test_save_report_absolute_path(self):
        reporter = RepoReporter(self.repo_path)
        abs_dir = os.path.abspath(f"abs_dir_{uuid.uuid4().hex[:8]}")
        filename = f"abs_report_{uuid.uuid4().hex[:6]}.txt"
        file_path = os.path.join(abs_dir, filename)
        content = "".join(random.choices(string.ascii_letters + string.digits, k=25))

        try:
            full_path = reporter.save_report(file_path, content)
            self.assertEqual(full_path, file_path)
            self.assertTrue(os.path.exists(full_path))
            with open(full_path, 'r', encoding='utf-8') as f:
                self.assertEqual(f.read(), content)
        finally:
            if os.path.exists(abs_dir):
                shutil.rmtree(abs_dir, ignore_errors=True)

    def test_generate_final_report(self):
        reporter = RepoReporter(self.repo_path)
        analytics_mock_val = f"analytics_{uuid.uuid4().hex[:8]}"
        summary_mock_val = f"summary_{uuid.uuid4().hex[:8]}"

        with patch("skills.repo_reporter.RepoAnalytics") as mock_analytics, \
             patch("skills.repo_reporter.RepoSummarizer") as mock_summarizer:
            
            instance_a = mock_analytics.return_value
            instance_a.get_report.return_value = analytics_mock_val

            instance_s = mock_summarizer.return_value
            instance_s.generate_summary.return_value = summary_mock_val

            result = reporter.generate_final_report()

            self.assertIn(analytics_mock_val, result)
            self.assertIn(summary_mock_val, result)

    def test_generate_report_custom_status_summary(self):
        reporter = RepoReporter(self.repo_path)
        status_val = f"status_{uuid.uuid4().hex[:6]}"
        summary_val = f"summary_{uuid.uuid4().hex[:6]}"
        out_filename = f"custom_out_{uuid.uuid4().hex[:6]}.txt"

        saved_path = reporter.generate_report(status=status_val, summary=summary_val, output_path=out_filename)
        
        self.assertTrue(os.path.exists(saved_path))
        with open(saved_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn(status_val, content)
        self.assertIn(summary_val, content)

    def test_generate_report_default_path(self):
        reporter = RepoReporter(self.repo_path)
        status_val = f"st_{uuid.uuid4().hex[:6]}"
        summary_val = f"su_{uuid.uuid4().hex[:6]}"

        saved_path = reporter.generate_report(status=status_val, summary=summary_val)
        
        expected_default = os.path.join(self.repo_path, "report.txt")
        self.assertEqual(saved_path, expected_default)
        self.assertTrue(os.path.exists(saved_path))
        
        with open(saved_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn(status_val, content)
        self.assertIn(summary_val, content)


if __name__ == "__main__":
    unittest.main()