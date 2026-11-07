import os
import shutil
import unittest
import uuid
from skills.repo_reporter import RepoReporter


class TestRepoReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.repo_path = os.path.abspath(f"./test_repo_{self.rand_suffix}")
        if os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path)
        os.makedirs(self.repo_path, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path)

    def test_repo_reporter_integration_flow(self):
        reporter = RepoReporter(self.repo_path)
        
        test_status = f"STATUS_{uuid.uuid4().hex}"
        test_summary = f"SUMMARY_{uuid.uuid4().hex}"
        custom_report_name = f"report_{uuid.uuid4().hex[:6]}.txt"
        
        saved_file_path = reporter.generate_report(
            status=test_status,
            summary=test_summary,
            output_path=custom_report_name
        )

        self.assertTrue(os.path.isabs(saved_file_path))
        self.assertTrue(os.path.exists(saved_file_path))

        with open(saved_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(test_status, content)
        self.assertIn(test_summary, content)

        auto_final_report_path = reporter.generate_report()
        self.assertTrue(os.path.exists(auto_final_report_path))
        
        with open(auto_final_report_path, "r", encoding="utf-8") as f:
            auto_content = f.read()

        self.assertGreater(len(auto_content), 0)


if __name__ == "__main__":
    unittest.main()