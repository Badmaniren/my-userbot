import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.dependency_audit_exporter import DependencyAuditExporter


class TestDependencyAuditExporter(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex[:8]}"
        self.branch = f"branch-{uuid.uuid4().hex[:6]}"
        self.stream_source = f"stream-{uuid.uuid4().hex[:6]}"
        self.output_report_name = f"report-{uuid.uuid4().hex[:8]}.json"
        self.cve_identifier = f"CVE-{random.randint(2000, 2024)}-{random.randint(1000, 99999)}"
        self.target_version = f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}"

    @patch('skills.dependency_audit_exporter.aggregate_dependencies')
    @patch('skills.dependency_audit_exporter.DependencyAuditReporter')
    def test_export_audit_data_success(self, mock_reporter_class, mock_aggregate):
        random_summary_key = uuid.uuid4().hex[:10]
        random_summary_val = uuid.uuid4().hex[:10]
        mock_aggregate.return_value = {random_summary_key: random_summary_val}

        mock_reporter_instance = mock_reporter_class.return_value
        random_report_content = uuid.uuid4().bytes
        mock_reporter_instance.generate_audit_report.return_value = random_report_content

        exporter = DependencyAuditExporter(repo_path=self.repo_path)
        result = exporter.export_audit_data(
            branch=self.branch,
            stream_source=self.stream_source,
            output_report_name=self.output_report_name,
            cve_identifier=self.cve_identifier,
            target_version=self.target_version
        )

        mock_aggregate.assert_called_once_with(
            repo_path=self.repo_path,
            output_report_name=self.output_report_name,
            cve_identifier=self.cve_identifier,
            target_version=self.target_version
        )
        mock_reporter_class.assert_called_once_with(repo_path=self.repo_path)
        mock_reporter_instance.generate_audit_report.assert_called_once_with(
            branch=self.branch,
            stream_source=self.stream_source,
            output_report_name=self.output_report_name,
            cve_identifier=self.cve_identifier,
            target_version=self.target_version
        )
        self.assertEqual(result, random_report_content)

    @patch('skills.dependency_audit_exporter.aggregate_dependencies')
    @patch('skills.dependency_audit_exporter.DependencyAuditReporter')
    def test_export_custom_audit_report(self, mock_reporter_class, mock_aggregate):
        status_val = random.choice(['SUCCESS', 'FAILED', 'WARNING', uuid.uuid4().hex[:5]])
        summary_dict = {uuid.uuid4().hex[:6]: uuid.uuid4().hex[:6]}
        output_path = f"/path/to/{uuid.uuid4().hex[:8]}.log"

        mock_reporter_instance = mock_reporter_class.return_value
        random_save_path = f"/saved/{uuid.uuid4().hex[:8]}.json"
        mock_reporter_instance.create_custom_report.return_value = random_save_path

        exporter = DependencyAuditExporter(repo_path=self.repo_path)
        res_path = exporter.export_custom_report(
            status=status_val,
            summary=summary_dict,
            output_path=output_path
        )

        mock_reporter_class.assert_called_once_with(repo_path=self.repo_path)
        mock_reporter_instance.create_custom_report.assert_called_once_with(
            status=status_val,
            summary=summary_dict,
            output_path=output_path
        )
        self.assertEqual(res_path, random_save_path)

    @patch('skills.dependency_audit_exporter.aggregate_dependencies')
    @patch('skills.dependency_audit_exporter.DependencyAuditReporter')
    def test_save_exported_audit_report(self, mock_reporter_class, mock_aggregate):
        file_path = f"/exports/{uuid.uuid4().hex[:8]}.txt"
        report_content = io.BytesIO(uuid.uuid4().bytes)

        mock_reporter_instance = mock_reporter_class.return_value
        exporter = DependencyAuditExporter(repo_path=self.repo_path)
        exporter.save_exported_report(file_path=file_path, report_content=report_content)

        mock_reporter_instance.save_audit_report.assert_called_once_with(
            file_path=file_path,
            report_content=report_content
        )


if __name__ == '__main__':
    unittest.main()