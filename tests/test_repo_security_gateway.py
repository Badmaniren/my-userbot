import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.repo_security_gateway import RepoSecurityGateway


class TestRepoSecurityGateway(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.gateway = RepoSecurityGateway(self.repo_path)

    def test_start_new_success_flow(self):
        random_score = random.randint(1, 100)
        random_report_id = uuid.uuid4().hex
        random_stream_data = f"dependency_id:{random_report_id}".encode('utf-8')

        with patch('skills.repo_security_gateway.DependencyScanner') as MockScanner, \
             patch('skills.repo_security_gateway.VulnerabilityAnalyzer') as MockAnalyzer, \
             patch('skills.repo_security_gateway.RepoReporter') as MockReporter:

            scanner_instance = MockScanner.return_value
            scanner_instance.run.return_value = io.BytesIO(random_stream_data)

            analyzer_instance = MockAnalyzer.return_value
            analyzer_instance.run.return_value = {
                "risk_score": random_score,
                "report_id": random_report_id
            }

            reporter_instance = MockReporter.return_value
            expected_output_path = f"/reports/{uuid.uuid4().hex}.pdf"
            reporter_instance.generate_report.return_value = expected_output_path

            result = self.gateway.start_new()

            MockScanner.assert_called_once_with(self.repo_path)
            scanner_instance.run.assert_called_once()

            MockAnalyzer.assert_called_once_with(self.repo_path)
            analyzer_instance.run.assert_called_once()

            MockReporter.assert_called_once_with(self.repo_path)
            reporter_instance.generate_report.assert_called_once()

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("risk_score"), random_score)
            self.assertEqual(result.get("report_path"), expected_output_path)
            self.assertEqual(result.get("status"), "secure_gateway_passed")

    def test_start_new_high_vulnerability_failure(self):
        danger_score = random.randint(85, 100)
        random_error_token = ''.join(random.choices(string.ascii_letters, k=10))

        with patch('skills.repo_security_gateway.DependencyScanner') as MockScanner, \
             patch('skills.repo_security_gateway.VulnerabilityAnalyzer') as MockAnalyzer, \
             patch('skills.repo_security_gateway.RepoLogger') as MockLogger:

            scanner_instance = MockScanner.return_value
            scanner_instance.run.return_value = io.BytesIO(b"stream_payload")

            analyzer_instance = MockAnalyzer.return_value
            analyzer_instance.run.return_value = {
                "risk_score": danger_score,
                "error_token": random_error_token
            }

            logger_instance = MockLogger.return_value

            result = self.gateway.start_new()

            logger_instance.log_error.assert_called()
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("risk_score"), danger_score)
            self.assertEqual(result.get("status"), "blocked_by_security_gateway")
            self.assertIn("error_token", result)

    def test_start_new_exception_handling(self):
        random_exception_msg = f"Critical error code {random.randint(1000, 9999)}"

        with patch('skills.repo_security_gateway.DependencyScanner', side_effect=Exception(random_exception_msg)), \
             patch('skills.repo_security_gateway.RepoLogger') as MockLogger:

            logger_instance = MockLogger.return_value

            result = self.gateway.start_new()

            logger_instance.log_error.assert_called()
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("status"), "failed")
            self.assertIn(random_exception_msg, result.get("error"))


if __name__ == '__main__':
    unittest.main()