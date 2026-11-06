import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.dependency_audit_pipeline import run_dependency_audit_pipeline


class TestDependencyAuditPipeline(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.branch = "".join(random.choices(string.ascii_lowercase, k=8))
        self.stream = "".join(random.choices(string.ascii_lowercase, k=6))
        self.cve = f"CVE-{random.randint(2000, 2026)}-{random.randint(1000, 9999)}"
        self.version = f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.report_name = f"report_{uuid.uuid4().hex}.json"

    def test_pipeline_success_flow(self):
        chaos_summary = f"Audit passed with random token {uuid.uuid4().hex}"
        chaos_status = "SECURE"
        chaos_report_path = f"/reports/{uuid.uuid4().hex}.json"

        with patch("skills.dependency_audit_pipeline.dependency_audit_guardian") as mock_guardian, \
             patch("skills.dependency_audit_pipeline.DependencyAuditReporter") as mock_reporter_cls:

            mock_guardian.execute_guarded_audit.return_value = True

            mock_reporter_instance = mock_reporter_cls.return_value
            mock_reporter_instance.generate_audit_report.return_value = True
            mock_reporter_instance.create_custom_report.return_value = chaos_report_path

            result = run_dependency_audit_pipeline(
                repo_path=self.repo_path,
                branch=self.branch,
                stream_source=self.stream,
                cve_identifier=self.cve,
                target_version=self.version,
                output_report_name=self.report_name
            )

            mock_guardian.execute_guarded_audit.assert_called_once_with(
                repo=self.repo_path,
                report=self.report_name,
                cve=self.cve,
                version=self.version,
                branch=self.branch,
                stream=self.stream
            )

            mock_reporter_cls.assert_called_once_with(repo_path=self.repo_path)
            mock_reporter_instance.generate_audit_report.assert_called_once_with(
                branch=self.branch,
                stream_source=self.stream,
                output_report_name=self.report_name,
                cve_identifier=self.cve,
                target_version=self.version
            )

            self.assertTrue(result)

    def test_pipeline_guardian_failure(self):
        with patch("skills.dependency_audit_pipeline.dependency_audit_guardian") as mock_guardian, \
             patch("skills.dependency_audit_pipeline.DependencyAuditReporter") as mock_reporter_cls:

            mock_guardian.execute_guarded_audit.return_value = False

            result = run_dependency_audit_pipeline(
                repo_path=self.repo_path,
                branch=self.branch,
                stream_source=self.stream,
                cve_identifier=self.cve,
                target_version=self.version,
                output_report_name=self.report_name
            )

            mock_guardian.execute_guarded_audit.assert_called_once()
            mock_reporter_cls.assert_not_called()
            self.assertFalse(result)

    def test_pipeline_reporter_exception_handling(self):
        with patch("skills.dependency_audit_pipeline.dependency_audit_guardian") as mock_guardian, \
             patch("skills.dependency_audit_pipeline.DependencyAuditReporter") as mock_reporter_cls:

            mock_guardian.execute_guarded_audit.return_value = True

            mock_reporter_instance = mock_reporter_cls.return_value
            mock_reporter_instance.generate_audit_report.side_effect = Exception(f"Chaos error {uuid.uuid4().hex}")

            result = run_dependency_audit_pipeline(
                repo_path=self.repo_path,
                branch=self.branch,
                stream_source=self.stream,
                cve_identifier=self.cve,
                target_version=self.version,
                output_report_name=self.report_name
            )

            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()