import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from skills.dependency_audit_reporter import DependencyAuditReporter


class TestDependencyAuditReporter(unittest.TestCase):

    def setUp(self):
        self.reporter = DependencyAuditReporter()
        self.random_epic_id = uuid.uuid4().hex
        self.random_vuln_count = random.randint(1, 100)
        self.random_pkg_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_version = f"{random.randint(0, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.random_cve = f"CVE-{random.randint(2000, 2024)}-{random.randint(1000, 9999)}"

    def test_generate_report_success_logic(self):
        audit_data = {
            "epic_id": self.random_epic_id,
            "vulnerabilities_found": self.random_vuln_count,
            "package": self.random_pkg_name,
            "version": self.random_version,
            "cve": self.random_cve
        }

        with patch('skills.dependency_audit_reporter.datetime') as mock_datetime:
            random_timestamp = uuid.uuid4().hex
            mock_datetime.now.return_value.isoformat.return_value = random_timestamp
            
            report = self.reporter.generate_report(audit_data)

            self.assertIn(self.random_epic_id, report)
            self.assertIn(str(self.random_vuln_count), report)
            self.assertIn(self.random_pkg_name, report)
            self.assertIn(self.random_cve, report)
            self.assertIn(random_timestamp, report)

    def test_finalize_epic_audit_with_stream(self):
        random_stream_data = f"AUDIT_LOG_{uuid.uuid4().hex}_STATUS_OK".encode('utf-8')
        mock_stream = io.BytesIO(random_stream_data)

        with patch('skills.dependency_audit_reporter.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = self.reporter.finalize_epic(self.random_epic_id, mock_stream)

            self.assertTrue(result)
            mock_open.assert_called_once()
            mock_file.write.assert_called_once_with(random_stream_data)

    def test_audit_report_failure_handling(self):
        malformed_data = {
            "corrupted_key": uuid.uuid4().hex,
            "error_code": random.randint(500, 999)
        }

        with patch('skills.dependency_audit_reporter.sys.stderr', new=io.StringIO()) as mock_stderr:
            report = self.reporter.generate_report(malformed_data)
            
            self.assertIsNotNone(report)
            self.assertIn("ERROR", report)
            self.assertIn(str(malformed_data["error_code"]), report)

    def test_export_audit_summary_json(self):
        summary_payload = {
            "audit_uuid": uuid.uuid4().hex,
            "score": random.uniform(0.0, 10.0),
            "status": random.choice(["SECURE", "VULNERABLE", "CRITICAL"])
        }

        json_output = self.reporter.export_summary(summary_payload, format="json")

        self.assertIn(summary_payload["audit_uuid"], json_output)
        self.assertIn(str(summary_payload["score"]), json_output)
        self.assertIn(summary_payload["status"], json_output)
        self.assertTrue(json_output.startswith("{") or json_output.startswith("