import unittest
from unittest.mock import patch
import uuid
import random
import string
from skills.repo_security_gateway import RepoSecurityGateway


class TestRepoSecurityGateway(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/repo/{uuid.uuid4().hex}/{''.join(random.choices(string.ascii_lowercase, k=6))}"
        self.gateway = RepoSecurityGateway(self.random_repo_path)

    def test_init_sets_repo_path(self):
        expected_path = f"/var/git/{uuid.uuid4().hex}"
        gateway = RepoSecurityGateway(expected_path)
        self.assertEqual(gateway.repo_path, expected_path)

    def test_start_new_high_risk_blocked(self):
        risk_score = random.randint(85, 100)
        error_token = uuid.uuid4().hex
        
        analysis_result = {
            "risk_score": risk_score,
            "error_token": error_token
        }

        with patch("skills.repo_security_gateway.DependencyScanner") as MockScanner, \
             patch("skills.repo_security_gateway.VulnerabilityAnalyzer") as MockAnalyzer, \
             patch("skills.repo_security_gateway.RepoLogger") as MockLogger:

            mock_scanner_instance = MockScanner.return_value
            mock_scanner_instance.run.return_value = {"dependencies": [uuid.uuid4().hex]}

            mock_analyzer_instance = MockAnalyzer.return_value
            mock_analyzer_instance.run.return_value = analysis_result

            mock_logger_instance = MockLogger.return_value

            result = self.gateway.start_new()

            MockScanner.assert_called_once_with(self.random_repo_path)
            MockAnalyzer.assert_called_once_with(self.random_repo_path)
            mock_logger_instance.log_error.assert_called_once_with(
                f"High vulnerability risk score detected: {risk_score}"
            )

            self.assertEqual(result["risk_score"], risk_score)
            self.assertEqual(result["status"], "blocked_by_security_gateway")
            self.assertEqual(result["error_token"], error_token)

    def test_start_new_secure_passed(self):
        risk_score = random.randint(0, 84)
        expected_report_path = f"/reports/{uuid.uuid4().hex}.pdf"
        
        analysis_result = {
            "risk_score": risk_score
        }

        with patch("skills.repo_security_gateway.DependencyScanner") as MockScanner, \
             patch("skills.repo_security_gateway.VulnerabilityAnalyzer") as MockAnalyzer, \
             patch("skills.repo_security_gateway.RepoReporter") as MockReporter:

            mock_scanner_instance = MockScanner.return_value
            mock_scanner_instance.run.return_value = {}

            mock_analyzer_instance = MockAnalyzer.return_value
            mock_analyzer_instance.run.return_value = analysis_result

            mock_reporter_instance = MockReporter.return_value
            mock_reporter_instance.generate_report.return_value = expected_report_path

            result = self.gateway.start_new()

            MockReporter.assert_called_once_with(self.random_repo_path)
            mock_reporter_instance.generate_report.assert_called_once()

            self.assertEqual(result["risk_score"], risk_score)
            self.assertEqual(result["report_path"], expected_report_path)
            self.assertEqual(result["status"], "secure_gateway_passed")

    def test_start_new_exception_handled(self):
        error_message = f"Critical failure: {uuid.uuid4().hex}"

        with patch("skills.repo_security_gateway.DependencyScanner") as MockScanner, \
             patch("skills.repo_security_gateway.RepoLogger") as MockLogger:

            mock_scanner_instance = MockScanner.return_value
            mock_scanner_instance.run.side_effect = Exception(error_message)

            mock_logger_instance = MockLogger.return_value

            result = self.gateway.start_new()

            MockLogger.assert_called_once_with(self.random_repo_path)
            mock_logger_instance.log_error.assert_called_once_with(error_message)

            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["error"], error_message)

    def test_run_alias_calls_start_new(self):
        expected_result = {
            "status": uuid.uuid4().hex,
            "risk_score": random.randint(0, 100)
        }

        with patch.object(RepoSecurityGateway, "start_new", return_value=expected_result) as mock_start:
            result = self.gateway.run()
            mock_start.assert_called_once()
            self.assertEqual(result, expected_result)

    def test_scan_and_evaluate_alias_calls_start_new(self):
        expected_result = {
            "status": uuid.uuid4().hex,
            "risk_score": random.randint(0, 100)
        }

        with patch.object(RepoSecurityGateway, "start_new", return_value=expected_result) as mock_start:
            result = self.gateway.scan_and_evaluate()
            mock_start.assert_called_once()
            self.assertEqual(result, expected_result)


if __name__ == "__main__":
    unittest.main()