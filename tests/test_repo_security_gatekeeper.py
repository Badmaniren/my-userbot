import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.repo_security_gatekeeper import start_new


class TestRepoSecurityGatekeeper(unittest.TestCase):

    def setUp(self):
        self.random_repo = ''.join(random.choices(string.ascii_lowercase, k=10)) + "_" + uuid.uuid4().hex[:8]
        self.random_branch = "feature/" + uuid.uuid4().hex[:6]
        self.random_vuln_id = "CVE-" + str(random.randint(2000, 2026)) + "-" + str(random.randint(1000, 99999))
        self.random_url = f"https://repo.internal/{uuid.uuid4().hex}.git"

    def test_start_new_success_flow(self):
        scan_output = f"SCAN_REPORT: {self.random_vuln_id} detected in {self.random_repo}"
        mock_response = io.BytesIO(scan_output.encode('utf-8'))

        with patch('skills.repo_security_gatekeeper.repo_scanner', create=True) as mock_scanner, \
             patch('skills.repo_security_gatekeeper.vulnerability_analyzer', create=True) as mock_analyzer, \
             patch('skills.repo_security_gatekeeper.repo_logger', create=True) as mock_logger:

            mock_scanner.return_value = mock_response
            mock_analyzer.analyze.return_value = {"status": "clean", "target": self.random_repo}

            result = start_new(self.random_repo, branch=self.random_branch, remote_url=self.random_url)

            self.assertIsInstance(result, dict)
            self.assertIn("status", result)
            self.assertEqual(result.get("target"), self.random_repo)
            mock_logger.info.assert_called()

    def test_start_new_security_failure_detected(self):
        critical_error_msg = f"CRITICAL_VULNERABILITY_{uuid.uuid4().hex}"
        mock_stream = io.BytesIO(critical_error_msg.encode('utf-8'))

        with patch('skills.repo_security_gatekeeper.repo_scanner', create=True) as mock_scanner, \
             patch('skills.repo_security_gatekeeper.vulnerability_security_gate', create=True) as mock_gate, \
             patch('skills.repo_security_gatekeeper.repo_notifier', create=True) as mock_notifier:

            mock_scanner.return_value = mock_stream
            mock_gate.evaluate.side_effect = Exception(critical_error_msg)

            with self.assertRaises(Exception) as ctx:
                start_new(self.random_repo, fail_fast=True)

            self.assertIn(critical_error_msg, str(ctx.exception))
            mock_notifier.alert.assert_called()

    def test_start_new_pipeline_orchestration(self):
        random_pipeline_id = uuid.uuid4().hex
        mock_pipeline_result = {
            "pipeline_id": random_pipeline_id,
            "repository": self.random_repo,
            "audited": True
        }

        with patch('skills.repo_security_gatekeeper.repo_ci_pipeline', create=True) as mock_ci, \
             patch('skills.repo_security_gatekeeper.dependency_audit_pipeline', create=True) as mock_dep_pipeline:

            mock_ci.run.return_value = mock_pipeline_result
            mock_dep_pipeline.execute.return_value = True

            result = start_new(self.random_repo, run_ci=True)

            self.assertEqual(result.get("pipeline_id"), random_pipeline_id)
            self.assertTrue(result.get("audited"))
            mock_ci.run.assert_called_once()
            mock_dep_pipeline.execute.assert_called_once()

    def test_start_new_with_random_recovery_action(self):
        random_error_code = random.randint(500, 599)
        mock_stream = io.BytesIO(b"")

        with patch('skills.repo_security_gatekeeper.repo_scanner', create=True) as mock_scanner, \
             patch('skills.repo_security_gatekeeper.repo_recovery', create=True) as mock_recovery:

            mock_scanner.return_value = mock_stream
            mock_scanner.side_effect = ConnectionError(f"Gateway timeout {random_error_code}")

            mock_recovery.restore.return_value = {"recovered": True, "code": random_error_code}

            result = start_new(self.random_repo, auto_recover=True)

            self.assertTrue(result.get("recovered"))
            self.assertEqual(result.get("code"), random_error_code)
            mock_recovery.restore.assert_called_once()


if __name__ == '__main__':
    unittest.main()