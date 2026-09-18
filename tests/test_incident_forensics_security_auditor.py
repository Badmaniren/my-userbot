import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.incident_forensics_security_auditor import IncidentForensicsSecurityAuditor

class TestIncidentForensicsSecurityAuditor(unittest.TestCase):

    def setUp(self):
        self.auditor = IncidentForensicsSecurityAuditor()
        self.random_prefix = uuid.uuid4().hex[:8]
        self.log_path = f"/var/log/security_{self.random_prefix}.log"
        self.compromised_signature = f"SIG_BREACH_{uuid.uuid4().hex.upper()}"
        self.clean_signature = f"SIG_CLEAN_{uuid.uuid4().hex.upper()}"

    def test_audit_logs_unauthorized_changes_detected(self):
        malicious_entry = f"[{random.randint(1000, 9999)}] UNAUTHORIZED ROOT ACCESS DETECTED: {self.compromised_signature}"
        mock_file_content = io.BytesIO(malicious_entry.encode('utf-8'))

        with patch('builtins.open', return_value=mock_file_content) as mock_open:
            result = self.auditor.audit_forensics_log(self.log_path)

            mock_open.assert_called_once_with(self.log_path, 'rb')
            self.assertIsInstance(result, dict)
            self.assertIn('status', result)
            self.assertEqual(result['status'], 'COMPROMISED')
            self.assertIn(self.compromised_signature, result['evidence'])

    def test_audit_logs_clean_system(self):
        clean_entry = f"[{random.randint(1000, 9999)}] System normal, integrity verified: {self.clean_signature}"
        mock_file_content = io.BytesIO(clean_entry.encode('utf-8'))

        with patch('builtins.open', return_value=mock_file_content) as mock_open:
            result = self.auditor.audit_forensics_log(self.log_path)

            mock_open.assert_called_once_with(self.log_path, 'rb')
            self.assertEqual(result['status'], 'SECURE')
            self.assertIn(self.clean_signature, result['evidence'])

    def test_verify_log_checksum_mismatch(self):
        expected_hash = uuid.uuid4().hex
        corrupted_data = "".join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')
        mock_file_content = io.BytesIO(corrupted_data)

        with patch('builtins.open', return_value=mock_file_content):
            is_valid = self.auditor.verify_log_checksum(self.log_path, expected_hash)
            self.assertFalse(is_valid)

    def test_extract_forensic_anomalies_success(self):
        anomaly_id = f"ANOMALY_{random.randint(10000, 99999)}"
        raw_telemetry = json.dumps({
            "event_id": anomaly_id,
            "threat_level": "CRITICAL",
            "vector": "".join(random.choices(string.ascii_lowercase, k=10))
        }).encode('utf-8')

        mock_file_content = io.BytesIO(raw_telemetry)

        with patch('builtins.open', return_value=mock_file_content):
            anomalies = self.auditor.extract_forensic_anomalies(self.log_path)
            self.assertTrue(len(anomalies) > 0)
            found = any(anomaly_id in str(item) for item in anomalies)
            self.assertTrue(found)

    def test_generate_forensics_report_structure(self):
        report_id = uuid.uuid4().hex
        analyst_name = f"Agent_{random.choice(['Alpha', 'Omega', 'Delta'])}"

        report = self.auditor.generate_forensics_report(report_id, analyst_name)

        self.assertIsInstance(report, dict)
        self.assertEqual(report['report_id'], report_id)
        self.assertEqual(report['auditor'], analyst_name)
        self.assertIn('timestamp', report)
        self.assertIn('verdict', report)

if __name__ == '__main__':
    unittest.main()