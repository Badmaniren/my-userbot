import unittest
from unittest.mock import patch, MagicMock
import tempfile
import uuid
import random
import os

from skills.release_automation_hub import ReleaseAutomationHub


class TestReleaseAutomationHub(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.tmp_dir.name
        self.output_filename = f"{uuid.uuid4().hex}.log"
        self.output_path = os.path.join(self.repo_path, self.output_filename)

    def tearDown(self):
        self.tmp_dir.cleanup()

    @patch('skills.release_automation_hub.RepoReporter')
    @patch('skills.release_automation_hub.ReleasePipeline')
    def test_release_automation_hub_success_flow(self, mock_release_pipeline_cls, mock_repo_reporter_cls):
        random_report_content = uuid.uuid4().hex

        mock_pipeline_instance = mock_release_pipeline_cls.return_value
        mock_pipeline_instance.run.return_value = True

        mock_reporter_instance = mock_repo_reporter_cls.return_value
        mock_reporter_instance.generate_final_report.return_value = random_report_content

        hub = ReleaseAutomationHub(repo_path=self.repo_path)
        success = hub.execute_release_cycle(self.output_path)

        self.assertTrue(success)
        mock_pipeline_instance.run.assert_called_once_with(self.output_path)
        mock_reporter_instance.generate_final_report.assert_called_once()
        mock_reporter_instance.save_report.assert_called_once_with(self.output_path, random_report_content)

    @patch('skills.release_automation_hub.RepoReporter')
    @patch('skills.release_automation_hub.ReleasePipeline')
    def test_release_automation_hub_failure_flow(self, mock_release_pipeline_cls, mock_repo_reporter_cls):
        random_report_content = uuid.uuid4().hex

        mock_pipeline_instance = mock_release_pipeline_cls.return_value
        mock_pipeline_instance.run.return_value = False

        mock_reporter_instance = mock_repo_reporter_cls.return_value
        mock_reporter_instance.generate_final_report.return_value = random_report_content

        hub = ReleaseAutomationHub(repo_path=self.repo_path)
        success = hub.execute_release_with_report(self.output_path)

        self.assertFalse(success)
        mock_pipeline_instance.run.assert_called_once_with(self.output_path)
        mock_reporter_instance.generate_final_report.assert_called_once()
        mock_reporter_instance.save_report.assert_called_once_with(self.output_path, random_report_content)


if __name__ == '__main__':
    unittest.main()