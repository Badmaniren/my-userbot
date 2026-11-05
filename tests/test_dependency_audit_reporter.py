import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import os

from skills.dependency_audit_reporter import DependencyAuditReporter


class TestDependencyAuditReporter(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.branch = f"feature/{uuid.uuid4().hex[:8]}"
        self.stream_source = f"https://{uuid.uuid4().hex}.com/stream"
        self.output_report_name = f"report_{uuid.uuid4().hex}.json"
        self.cve_identifier = f"CVE-{random.randint(2000, 2024)}-{random.randint(1000, 9999)}"
        self.target_version = f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.status = f"status_{uuid.uuid4().hex[:6]}"
        self.summary = f"summary_{uuid.uuid4().hex[:10]}"
        self.output_path = f"/var/reports/{uuid.uuid4().hex}.html"
        self.file_path = f"/saved/{uuid.uuid4().hex}.txt"

    @patch('skills.dependency_audit_reporter.dependency_audit_aggregator')
    @patch('skills.dependency_audit_reporter.RepoReporter')
    def test_run_audit_and_report_success(self, mock_repo_reporter_cls, mock_aggregator):
        mock_reporter_instance = MagicMock()
        mock_repo_reporter_cls.return_value = mock_reporter_instance

        expected_audit_result = f"audit_data_{uuid.uuid4().hex}"
        mock_aggregator.aggregate_dependencies.return_value = expected_audit_result

        expected_final_report = f"report_content_{uuid.uuid4().hex}"
        mock_reporter_instance.generate_final_report.return_value = expected_final_report

        expected_saved_path = f"saved_path_{uuid.uuid4().hex}"
        mock_reporter_instance.save_report.return_value = expected_saved_path

        reporter = DependencyAuditReporter(self.repo_path)
        result = reporter.generate_audit_report(
            branch=self.branch,
            stream_source=self.stream_source,
            output_report_name=self.output_report_name,
            cve_identifier=self.cve_identifier,
            target_version=self.target_version
        )

        mock_aggregator.start_new.assert_called_once_with(
            self.repo_path, self.branch, self.stream_source
        )
        mock_aggregator.aggregate_dependencies.assert_called_once_with(
            self.repo_path, self.output_report_name, self.cve_identifier, self.target_version
        )
        mock_repo_reporter_cls.assert_called_once_with(self.repo_path)
        mock_reporter_instance.generate_final_report.assert_called_once()
        mock_reporter_instance.save_report.assert_called_once_with(
            self.output_report_name, expected_final_report
        )
        self.assertEqual(result, expected_saved_path)

    @patch('skills.dependency_audit_reporter.dependency_audit_aggregator')
    @patch('skills.dependency_audit_reporter.RepoReporter')
    def test_generate_custom_report(self, mock_repo_reporter_cls, mock_aggregator):
        mock_reporter_instance = MagicMock()
        mock_repo_reporter_cls.return_value = mock_reporter_instance

        expected_report_output = f"custom_report_{uuid.uuid4().hex}"
        mock_reporter_instance.generate_report.return_value = expected_report_output

        reporter = DependencyAuditReporter(self.repo_path)
        res = reporter.create_custom_report(
            status=self.status,
            summary=self.summary,
            output_path=self.output_path
        )

        mock_repo_reporter_cls.assert_called_once_with(self.repo_path)
        mock_reporter_instance.generate_report.assert_called_once_with(
            self.status, self.summary, self.output_path
        )
        self.assertEqual(res, expected_report_output)
        mock_aggregator.start_new.assert_not_called()

    @patch('skills.dependency_audit_reporter.dependency_audit_aggregator')
    @patch('skills.dependency_audit_reporter.RepoReporter')
    def test_aggregation_failure_propagates(self, mock_repo_reporter_cls, mock_aggregator):
        err_msg = f"Aggregation failed {uuid.uuid4().hex}"
        mock_aggregator.aggregate_dependencies.side_effect = RuntimeError(err_msg)

        reporter = DependencyAuditReporter(self.repo_path)
        with self.assertRaises(RuntimeError) as ctx:
            reporter.generate_audit_report(
                branch=self.branch,
                stream_source=self.stream_source,
                output_report_name=self.output_report_name,
                cve_identifier=self.cve_identifier,
                target_version=self.target_version
            )
        self.assertIn(err_msg, str(ctx.exception))

    @patch('skills.dependency_audit_reporter.RepoReporter')
    def test_io_stream_handling_in_reporter(self, mock_repo_reporter_cls):
        mock_reporter_instance = MagicMock()
        mock_repo_reporter_cls.return_value = mock_reporter_instance

        random_bytes = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)
        mock_reporter_instance.save_report.return_value = random_bytes.read().hex()

        reporter = DependencyAuditReporter(self.repo_path)
        report_content = f"content-{uuid.uuid4().hex}"
        
        res = reporter.save_audit_report(self.file_path, report_content)

        mock_reporter_instance.save_report.assert_called_once_with(self.file_path, report_content)
        self.assertIsInstance(res, str)


if __name__ == '__main__':
    unittest.main()