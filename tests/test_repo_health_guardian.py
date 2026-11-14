import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
from skills.repo_health_guardian import RepoHealthGuardian

class TestRepoHealthGuardian(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.guardian = RepoHealthGuardian(self.repo_path)

    @patch('skills.repo_health_guardian.RepoMonitor')
    @patch('skills.repo_health_guardian.RepoAuditor')
    @patch('skills.repo_health_guardian.RepoHealthPulseEngine')
    def test_check_health_and_audit(self, mock_pulse_engine_cls, mock_auditor_cls, mock_monitor_cls):
        random_status_key = uuid.uuid4().hex
        random_status_val = uuid.uuid4().hex
        random_audit_key = uuid.uuid4().hex
        random_audit_val = uuid.uuid4().hex
        random_pulse_key = uuid.uuid4().hex
        random_pulse_val = uuid.uuid4().hex

        mock_monitor = mock_monitor_cls.return_value
        mock_monitor.check_status.return_value = {random_status_key: random_status_val}

        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.audit.return_value = {random_audit_key: random_audit_val}

        mock_pulse = mock_pulse_engine_cls.return_value
        mock_pulse.verify_pulse.return_value = {random_pulse_key: random_pulse_val}

        result = self.guardian.check_health_and_audit()

        self.assertIn("status", result)
        self.assertIn("audit", result)
        self.assertIn("security_pulse", result)
        self.assertEqual(result["status"][random_status_key], random_status_val)
        self.assertEqual(result["audit"][random_audit_key], random_audit_val)
        self.assertEqual(result["security_pulse"][random_pulse_key], random_pulse_val)

        mock_monitor.check_status.assert_called_once()
        mock_auditor.audit.assert_called_once()
        mock_pulse.verify_pulse.assert_called_once()

    @patch('skills.repo_health_guardian.RepoMonitor')
    @patch('skills.repo_health_guardian.RepoAuditor')
    @patch('skills.repo_health_guardian.RepoHealthPulseEngine')
    def test_run_preventive_maintenance(self, mock_pulse_engine_cls, mock_auditor_cls, mock_monitor_cls):
        issue_id = uuid.uuid4().hex
        mock_monitor = mock_monitor_cls.return_value
        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.detect_issues.return_value = [issue_id]

        mock_pulse = mock_pulse_engine_cls.return_value
        mock_pulse.secure_sweep.return_value = True

        result = self.guardian.run_preventive_maintenance()

        self.assertIn("issues_detected", result)
        self.assertIn("action_taken", result)
        self.assertIn("security_sweep_passed", result)
        self.assertIn(issue_id, result["issues_detected"])
        self.assertTrue(result["action_taken"])
        self.assertTrue(result["security_sweep_passed"])

        mock_monitor.check_status.assert_called_once()
        mock_auditor.detect_issues.assert_called_once()
        mock_pulse.secure_sweep.assert_called_once()

    @patch('skills.repo_health_guardian.RepoAuditor')
    def test_analyze_repo_structure(self, mock_auditor_cls):
        struct_key = uuid.uuid4().hex
        struct_val = uuid.uuid4().hex

        mock_auditor = mock_auditor_cls.return_value
        mock_auditor.analyze_structure.return_value = {struct_key: struct_val}

        result = self.guardian.analyze_repo_structure()

        self.assertEqual(result[struct_key], struct_val)
        mock_auditor.analyze_structure.assert_called_once()

    @patch('skills.repo_health_guardian.RepoHealthPulseEngine')
    def test_enhanced_security_check(self, mock_pulse_engine_cls):
        token = uuid.uuid4().hex
        mock_pulse = mock_pulse_engine_cls.return_value
        mock_pulse.inspect_unauthorized_changes.return_value = {"unauthorized": False, "signature": token}

        if hasattr(self.guardian, "enhanced_security_check"):
            res = self.guardian.enhanced_security_check()
            self.assertFalse(res["unauthorized"])
            self.assertEqual(res["signature"], token)

    def test_stream_processing_compatibility(self):
        stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        if hasattr(self.guardian, "process_guardian_stream"):
            res = self.guardian.process_guardian_stream(stream_data)
            self.assertIsInstance(res, dict)

if __name__ == '__main__':
    unittest.main()