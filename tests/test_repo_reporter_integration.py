import os
import shutil
import unittest
import uuid
from skills.repo_reporter import RepoReporter
from skills.repo_analytics import RepoMonitor as RepoAnalytics
from skills.repo_summarizer import RepoSummarizer


class TestRepoReporterIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.abspath(f"test_repo_{uuid.uuid4().hex[:8]}")
        os.makedirs(self.test_dir, exist_ok=True)
        self.reporter = RepoReporter(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_integration_generate_and_save_report(self):
        unique_file_name = f"report_{uuid.uuid4().hex[:8]}.txt"
        unique_content_token = f"TOKEN_{uuid.uuid4().hex}"

        test_file_path = os.path.join(self.test_dir, f"source_{uuid.uuid4().hex[:6]}.py")
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(f"# {unique_content_token}\nprint('Integration test')\n")

        analytics = RepoAnalytics(self.test_dir)
        summarizer = RepoSummarizer(self.test_dir)

        expected_analytics = analytics.check_status()
        expected_summary = summarizer.generate_summary()

        saved_path = self.reporter.generate_report(output_path=unique_file_name)

        self.assertTrue(os.path.isabs(saved_path))
        self.assertTrue(os.path.exists(saved_path))
        self.assertEqual(os.path.basename(saved_path), unique_file_name)

        with open(saved_path, "r", encoding="utf-8") as f:
            file_content = f.read()

        self.assertIn(expected_analytics, file_content)
        self.assertIn(expected_summary, file_content)

    def test_integration_custom_status_and_summary(self):
        custom_status = f"STATUS_{uuid.uuid4().hex[:8]}"
        custom_summary = f"SUMMARY_{uuid.uuid4().hex[:8]}"
        output_name = f"custom_rep_{uuid.uuid4().hex[:6]}.log"

        saved_path = self.reporter.generate_report(
            status=custom_status,
            summary=custom_summary,
            output_path=output_name
        )

        self.assertTrue(os.path.exists(saved_path))

        with open(saved_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(custom_status, content)
        self.assertIn(custom_summary, content)


if __name__ == "__main__":
    unittest.main()