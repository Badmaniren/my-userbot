import os
import shutil
import unittest
import uuid
import random
from skills.repo_reporter import RepoReporter


class TestRepoReporterIntegration(unittest.TestCase):

    def setUp(self):
        self.unique_id = str(uuid.uuid4())
        self.repo_path = os.path.abspath(os.path.join("test_repo_" + self.unique_id))
        if os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path, ignore_errors=True)
        os.makedirs(self.repo_path, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path, ignore_errors=True)

    def test_generate_and_save_report_integration(self):
        reporter = RepoReporter(self.repo_path)
        
        random_status_val = f"STATUS_CHECK_{uuid.uuid4().hex[:8]}"
        random_summary_val = f"SUMMARY_CONTENT_{uuid.uuid4().hex[:8]}"
        custom_report_name = f"report_{uuid.uuid4().hex[:6]}.txt"
        
        saved_file_path = reporter.generate_report(
            status=random_status_val,
            summary=random_summary_val,
            output_path=custom_report_name
        )
        
        self.assertTrue(os.path.isabs(saved_file_path))
        self.assertTrue(os.path.exists(saved_file_path))
        
        with open(saved_file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
            
        self.assertIn(random_status_val, file_content)
        self.assertIn(random_summary_val, file_content)

    def test_automatic_final_report_generation(self):
        random_file_name = f"src_file_{uuid.uuid4().hex[:6]}.py"
        random_code_content = f"print('{uuid.uuid4()}')\n"
        
        file_full_path = os.path.join(self.repo_path, random_file_name)
        with open(file_full_path, 'w', encoding='utf-8') as f:
            f.write(random_code_content)
            
        reporter = RepoReporter(self.repo_path)
        
        final_report_path = reporter.generate_report()
        
        self.assertTrue(os.path.exists(final_report_path))
        
        with open(final_report_path, 'r', encoding='utf-8') as f:
            report_text = f.read()
            
        self.assertGreater(len(report_text), 0)


if __name__ == '__main__':
    unittest.main()