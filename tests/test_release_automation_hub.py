import unittest
from unittest.mock import patch
import uuid
import random
import string
import io
from skills.release_automation_hub import ReleaseAutomationHub


class TestReleaseAutomationHub(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.output_path = f"/reports/{uuid.uuid4().hex}.md"
        self.status = random.choice(["SUCCESS", "FAILURE", "WARNING", "CRITICAL"])
        self.summary = "".join(random.choices(string.ascii_letters + string.whitespace, k=30))
        self.report_content = f"# Report {uuid.uuid4().hex}\nStatus: {self.status}\nSummary: {self.summary}"

    def test_release_automation_hub_success_flow(self):
        hub = ReleaseAutomationHub(repo_path=self.repo_path)

        with patch("skills.release_automation_hub.ReleasePipeline") as mock_pipeline_cls, \
             patch("skills.release_automation_hub.RepoReporter") as mock_reporter_cls:

            mock_pipeline_instance = mock_pipeline_cls.return_value
            mock_pipeline_instance.run.return_value = True

            mock_reporter_instance = mock_reporter_cls.return_value
            mock_reporter_instance.generate_final_report.return_value = self.report_content
            mock_reporter_instance.save_report.return_value = self.output_path

            result = hub.execute_release_cycle(output_path=self.output_path)

            mock_pipeline_cls.assert_called_once_with(self.repo_path)
            mock_pipeline_instance.run.assert_called_once_with(self.output_path)
            mock_reporter_cls.assert_called_once_with(self.repo_path)
            mock_reporter_instance.generate_final_report.assert_called_once()
            mock_reporter_instance.save_report.assert_called_once_with(self.output_path, self.report_content)

            self.assertTrue(result)

    def test_release_automation_hub_failure_flow(self):
        hub = ReleaseAutomationHub(repo_path=self.repo_path)

        with patch("skills.release_automation_hub.ReleasePipeline") as mock_pipeline_cls, \
             patch("skills.release_automation_hub.RepoReporter") as mock_reporter_cls:

            mock_pipeline_instance = mock_pipeline_cls.return_