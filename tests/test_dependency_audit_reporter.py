import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.dependency_audit_reporter import generate_dependency_audit_report, generate_audit_report

class TestDependencyAuditReporter(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.output_report_name = f"report_{uuid.uuid4().hex}.json"
        self.cve_identifier = f"CVE-202{random.randint(0,9)}-{random.randint(1000, 9999)}"
        self.target_version = f"{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,9)}"
        self.branch = f"branch_{uuid.uuid4().hex[:8]}"
        self.stream_source = f"stream_{uuid.uuid4().hex[:8]}"

    @patch('skills.dependency_audit_reporter.aggregate_dependencies')
    @patch('skills.dependency_audit_reporter.RepoReporter')
    def test_generate_dependency_audit_report_composition(self, mock_repo_reporter_class, mock_aggregate_dependencies):
        expected_aggregation_result = {
            "status": uuid.uuid4().hex,
            "vulnerabilities_found": random.randint(0, 10)
        }
        mock_aggregate_dependencies.return_value = expected_aggregation_result

        expected_final_report = f"FINAL_REPORT_{uuid.uuid4().hex}"
        expected_report_path = f"/path/to/report_{uuid.uuid4().hex}.txt"

        mock_reporter_instance = MagicMock()
        mock_reporter_instance.generate_final_report.return_value = expected_final_report
        mock_reporter_instance.save_report.return_value = expected_report_path
        mock_repo_reporter_class.return_value = mock_reporter_instance

        result = generate_dependency_audit_report(
            self.repo_path,
            self.output_report_name,
            self.cve_identifier,
            self.target_version
        )

        mock_aggregate_dependencies.assert_called_once_with(
            self.repo_path,
            self.output_report_name,
            self.cve_identifier,
            self.target_version
        )

        mock_repo_reporter_class.assert_called_once_with(self.repo_path)
        mock_reporter_instance.generate_final_report.assert_called_once()
        mock_reporter_instance.save_report.assert_called_once()

        self.assertIsInstance(result, dict)
        self.assertEqual(result["report_path"], expected_report_path)
        self.assertEqual(result["aggregation_data"], expected_aggregation_result)
        self.assertEqual(result["final_report"], expected_final_report)

    @patch('skills.dependency_audit_reporter.aggregate_dependencies')
    @patch('skills.dependency_audit_reporter.RepoReporter')
    def test_generate_audit_report_compatibility_wrapper(self, mock_repo_reporter_class, mock_aggregate_dependencies):
        expected_aggregation_result = {
            "audited": ''.join(random.choices(string.ascii_letters, k=10))
        }
        mock_aggregate_dependencies.return_value = expected_aggregation_result

        expected_final_report = f"REPORT_CONTENT_{uuid.uuid4().hex}"

        mock_reporter_instance = MagicMock()
        mock_reporter_instance.generate_final_report.return_value = expected_final_report
        mock_repo_reporter_class.return_value = mock_reporter_instance

        result = generate_audit_report(
            self.repo_path,
            self.branch,
            self.stream_source,
            self.output_report_name,
            self.cve_identifier,
            self.target_version
        )

        mock_aggregate_dependencies.assert_called_once_with(
            self.repo_path,
            self.output_report_name,
            self.cve_identifier,
            self.target_version
        )

        mock_repo_reporter_class.assert_called_once_with(self.repo_path)
        mock_reporter_instance.generate_final_report.assert_called_once()
        mock_reporter_instance.save_report.assert_called_once()

        self.assertEqual(result, expected_final_report)

    @patch('skills.dependency_audit_reporter.aggregate_dependencies')
    @patch('skills.dependency_audit_reporter.RepoReporter')
    def test_reporter_initialization_with_exact_repo_path(self, mock_repo_reporter_class, mock_aggregate_dependencies):
        mock_aggregate_dependencies.return_value = {}
        mock_reporter_instance = MagicMock()
        mock_reporter_instance.generate_final_report.return_value = uuid.uuid4().hex
        mock_reporter_instance.save_report.return_value = uuid.uuid4().hex
        mock_repo_reporter_class.return_value = mock_reporter_instance

        generate_dependency_audit_report(
            self.repo_path,
            self.output_report_name,
            self.cve_identifier,
            self.target_version
        )

        mock_repo_reporter_class.assert_called_once_with(self.repo_path)

if __name__ == '__main__':
    unittest.main()