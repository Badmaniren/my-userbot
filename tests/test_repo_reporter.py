import os
import shutil
import tempfile
import unittest
import uuid
from unittest.mock import patch, MagicMock
from skills.repo_reporter import RepoReporter


class TestRepoReporter(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.repo_path = os.path.join(tempfile.gettempdir(), f"repo_test_{self.random_suffix}")
        os.makedirs(self.repo_path, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path, ignore_errors=True)

    def test_init_creates_git_dir(self):
        non_existent_repo = os.path.join(tempfile.gettempdir(), f"repo_non_{uuid.uuid4().hex[:8]}")
        try:
            reporter = RepoReporter(non_existent_repo)
            self.assertTrue(os.path.exists(os.path.join(non_existent_repo, ".git")))
        finally:
            if os.path.exists(non_existent_repo):
                shutil.rmtree(non_existent_repo, ignore_errors=True)

    def test_generate_final_report(self):
        analytics_text = f"analytics_metric_{uuid.uuid4().hex[:6]}"
        summary_text = f"summary_content_{uuid.uuid4().hex[:6]}"

        with patch("skills.repo_reporter.RepoAnalytics") as mock_analytics_cls, \
             patch("skills.repo_reporter.RepoSummarizer") as mock_summarizer_cls:
            
            mock_analytics_instance = mock_analytics_cls.return_value
            mock_analytics_instance.get_report.return_value = analytics_text

            mock_summarizer_instance = mock_summarizer_cls.return_value
            mock_summarizer_instance.generate_summary.return_value = summary_text

            reporter = RepoReporter(self.repo_path)
            report = reporter.generate_final_report()

            self.assertIn(analytics_text, report)
            self.assertIn(summary_text, report)

    def test_save_report_absolute_path(self):
        custom_file_name = f"report_{uuid.uuid4().hex[:6]}.txt"
        custom_dir = os.path.join(tempfile.gettempdir(), f"dir_{uuid.uuid4().hex[:6]}")
        abs_file_path = os.path.join(custom_dir, custom_file_name)
        file_content = f"content_{uuid.uuid4().hex}"

        try:
            reporter = RepoReporter(self.repo_path)
            saved_path = reporter.save_report(abs_file_path, file_content)

            self.assertEqual(saved_path, abs_file_path)
            self.assertTrue(os.path.exists(abs_file_path))

            with open(abs_file_path, "r", encoding="utf-8") as f:
                read_content = f.read()
            self.assertEqual(read_content, file_content)
        finally:
            if os.path.exists(custom_dir):
                shutil.rmtree(custom_dir, ignore_errors=True)

    def test_save_report_relative_path(self):
        rel_file_path = f"sub_{uuid.uuid4().hex[:4]}/report_{uuid.uuid4().hex[:4]}.txt"
        file_content = f"content_rel_{uuid.uuid4().hex}"

        reporter = RepoReporter(self.repo_path)
        saved_path = reporter.save_report(rel_file_path, file_content)

        expected_path = os.path.join(self.repo_path, rel_file_path)
        self.assertEqual(saved_path, expected_path)
        self.assertTrue(os.path.exists(expected_path))

        with open(expected_path, "r", encoding="utf-8") as f:
            read_content = f.read()
        self.assertEqual(read_content, file_content)

    def test_generate_report_default_path(self):
        final_report_text = f"final_mock_report_{uuid.uuid4().hex[:6]}"

        with patch.object(RepoReporter, "generate_final_report", return_value=final_report_text):
            reporter = RepoReporter(self.repo_path)
            output_path = reporter.generate_report()

            self.assertTrue(os.path.exists(output_path))
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertEqual(content, final_report_text)

    def test_generate_report_custom_status_summary(self):
        custom_status = f"status_{uuid.uuid4().hex[:6]}"
        custom_summary = f"summary_{uuid.uuid4().hex[:6]}"
        custom_output = f"custom_output_{uuid.uuid4().hex[:6]}.txt"

        reporter = RepoReporter(self.repo_path)
        output_path = reporter.generate_report(status=custom_status, summary=custom_summary, output_path=custom_output)

        self.assertTrue(os.path.exists(output_path))
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(custom_status, content)
        self.assertIn(custom_summary, content)