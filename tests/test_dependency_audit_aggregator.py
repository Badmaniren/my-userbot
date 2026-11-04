import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import string
from skills.dependency_audit_aggregator import start_new


class TestDependencyAuditAggregator(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/repo/{uuid.uuid4().hex[:10]}"
        self.random_branch = f"branch-{uuid.uuid4().hex[:8]}"
        self.random_vulnerability_id = f"CVE-{random.randint(2000, 2024)}-{random.randint(1000, 9999)}"
        self.random_package_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.random_old_version = f"{random.randint(0,2)}.{random.randint(0,9)}.{random.randint(0,9)}"
        self.random_new_version = f"{random.randint(3,5)}.{random.randint(0,9)}.{random.randint(0,9)}"

    def test_start_new_success_flow(self):
        with patch('skills.dependency_audit_aggregator.vulnerability_analyzer') as mock_vuln_analyzer, \
             patch('skills.dependency_audit_aggregator.dependency_updater_pipeline') as mock_updater_pipeline, \
             patch('skills.dependency_audit_aggregator.repo_reporter') as mock_reporter:

            mock_vuln_analyzer.scan_vulnerabilities.return_value = {
                "vulnerabilities": [
                    {
                        "id": self.random_vulnerability_id,
                        "package": self.random_package_name,
                        "severity": random.choice(["HIGH", "CRITICAL", "MODERATE"]),
                        "current_version": self.random_old_version
                    }
                ]
            }

            mock_updater_pipeline.run_update.return_value = {
                "updated_packages": [
                    {
                        "package": self.random_package_name,
                        "from_version": self.random_old_version,
                        "to_version": self.random_new_version,
                        "status": "SUCCESS"
                    }
                ]
            }

            expected_report_id = uuid.uuid4().hex
            mock_reporter.generate_aggregate_report.return_value = {
                "report_id": expected_report_id,
                "status": "COMPLETED"
            }

            result = start_new(
                repo_path=self.random_repo_path,
                branch=self.random_branch
            )

            mock_vuln_analyzer.scan_vulnerabilities.assert_called_once_with(self.random_repo_path)
            mock_updater_pipeline.run_update.assert_called_once_with(self.random_repo_path, self.random_branch)
            mock_reporter.generate_aggregate_report.assert_called_once()

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("report_id"), expected_report_id)
            self.assertEqual(result.get("status"), "COMPLETED")

    def test_start_new_no_vulnerabilities(self):
        with patch('skills.dependency_audit_aggregator.vulnerability_analyzer') as mock_vuln_analyzer, \
             patch('skills.dependency_audit_aggregator.dependency_updater_pipeline') as mock_updater_pipeline, \
             patch('skills.dependency_audit_aggregator.repo_reporter') as mock_reporter:

            mock_vuln_analyzer.scan_vulnerabilities.return_value = {"vulnerabilities": []}
            mock_updater_pipeline.run_update.return_value = {"updated_packages": []}
            
            fallback_message = f"clean-{uuid.uuid4().hex[:6]}"
            mock_reporter.generate_clean_report.return_value = {
                "message": fallback_message,
                "secure": True
            }

            result = start_new(repo_path=self.random_repo_path)

            mock_vuln_analyzer.scan_vulnerabilities.assert_called_once_with(self.random_repo_path)
            mock_updater_pipeline.run_update.assert_not_called()
            mock_reporter.generate_clean_report.assert_called_once()

            self.assertEqual(result.get("message"), fallback_message)
            self.assertTrue(result.get("secure"))

    def test_start_new_pipeline_exception_handling(self):
        random_error_msg = f"err-{uuid.uuid4().hex}"
        
        with patch('skills.dependency_audit_aggregator.vulnerability_analyzer') as mock_vuln_analyzer, \
             patch('skills.dependency_audit_aggregator.dependency_updater_pipeline') as mock_updater_pipeline, \
             patch('skills.dependency_audit_aggregator.repo_logger') as mock_logger:

            mock_vuln_analyzer.scan_vulnerabilities.side_effect = Exception(random_error_msg)

            with self.assertRaises(Exception) as ctx:
                start_new(repo_path=self.random_repo_path, branch=self.random_branch)

            self.assertIn(random_error_msg, str(ctx.exception))
            mock_logger.error.assert_called()

    def test_start_new_io_stream_handling(self):
        random_stream_data = f"audit-stream-{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(random_stream_data)

        with patch('skills.dependency_audit_aggregator.vulnerability_analyzer') as mock_vuln_analyzer, \
             patch('skills.dependency_audit_aggregator.dependency_updater_pipeline') as mock_updater_pipeline, \
             patch('skills.dependency_audit_aggregator.repo_reporter') as mock_reporter:

            mock_vuln_analyzer.scan_from_stream.return_value = {
                "stream_data_read": mock_stream.read().decode('utf-8'),
                "vulnerabilities": []
            }

            mock_reporter.generate_clean_report.return_value = {"status": "OK"}

            result = start_new(repo_path=self.random_repo_path, stream_source=mock_stream)

            mock_vuln_analyzer.scan_from_stream.assert_called_once()
            self.assertEqual(result.get("status"), "OK")