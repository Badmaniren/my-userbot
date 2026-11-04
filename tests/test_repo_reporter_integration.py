import os
import unittest
import uuid
import tempfile
from skills.repo_reporter import RepoReporter
from skills.repo_analytics import RepoMonitor
from skills.repo_summarizer import RepoSummarizer


class TestRepoReporterIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.reporter = RepoReporter(self.repo_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_generate_and_save_report(self):
        unique_marker = str(uuid.uuid4())
        test_file_name = f"test_file_{unique_marker}.txt"
        test_file_path = os.path.join(self.repo_path, test_file_name)
        
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(f"Integration content {unique_marker}")

        final_report = self.reporter.generate_final_report()
        self.assertIsInstance(final_report, str)

        output_filename = f"report_{unique_marker}.txt"
        saved_path = self.reporter.generate_report(output_path=output_filename)

        self.assertTrue(os.path.exists(saved_path))
        
        with open(saved_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(unique_marker, content)
        self.assertIn(final_report, content)


if __name__ == "__main__":
    unittest.main()