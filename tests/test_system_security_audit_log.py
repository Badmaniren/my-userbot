import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string

from skills.system_security_audit_log import SystemSecurityAuditLog

class TestSystemSecurityAuditLog(unittest.TestCase):

    def setUp(self):
        self.audit_log = SystemSecurityAuditLog()

    def test_collect_audit_event_success(self):
        random_event_id = uuid.uuid4().hex
        random_severity = random.choice(["INFO", "WARNING", "CRITICAL", "FATAL"])
        random_component = "".join(random.choices(string.ascii_lowercase, k=10))
        random_message = f"Audit incident payload {uuid.uuid4().hex}"

        mock_storage = MagicMock()
        with patch("skills.system_security_audit_log.open", create=True) as mock_file:
            mock_file.return_value = io.BytesIO(b"")
            result = self.audit_log.collect_event(
                event_id=random_event_id,
                severity=random_severity,
                component=random_component,
                message=random_message
            )

        self.assertIsNotNone(result)
        self.assertIn(random_event_id, str(result))

    def test_structuring_audit_logs_chaos(self):
        random_entries_count = random.randint(5, 15)
        raw_entries = []
        for _ in range(random_entries_count):
            raw_entries.append({
                "id": uuid.uuid4().hex,
                "code": random.randint(100, 999),
                "payload": uuid.uuid4().hex
            })

        structured_output = self.audit_log.structure_logs(raw_entries)

        self.assertIsInstance(structured_output, dict)
        self.assertIn("total_processed", structured_output)
        self.assertEqual(structured_output["total_processed"], random_entries_count)
        self.assertIn("entries", structured_output)
        self.assertEqual(len(structured_output["entries"]), random_entries_count)

        # Check integrity of data preservation
        matched = False
        for entry in structured_output["entries"]:
            if entry["id"] == raw_entries[0]["id"]:
                self.assertEqual(entry["code"], raw_entries[0]["code"])
                self.assertEqual(entry["payload"], raw_entries[0]["payload"])
                matched = True
                break
        self.assertTrue(matched, "Structured logs failed to preserve random input identity.")

    def test_export_audit_logs_to_stream(self):
        random_export_format = random.choice(["json", "csv", "syslog"])
        random_destination = f"/var/log/security_{uuid.uuid4().hex}.log"

        mock_stream = MagicMock()
        mock_stream.write.return_value = len(random_destination)

        with patch("skills.system_security_audit_log.open", create=True) as mock_file_open:
            mock_file_open.return_value = mock_stream
            export_status = self.audit_log.export_logs(
                export_format=random_export_format,
                destination_path=random_destination
            )

        self.assertTrue(export_status)
        mock_stream.write.assert_called()

    def test_audit_log_filtering_by_severity(self):
        target_severity = "CRITICAL"
        noise_severities = ["DEBUG", "INFO", "WARNING"]

        test_dataset = [
            {"id": uuid.uuid4().hex, "severity": target_severity, "msg": uuid.uuid4().hex},
            {"id": uuid.uuid4().hex, "severity": random.choice(noise_severities), "msg": uuid.uuid4().hex},
            {"id": uuid.uuid4().hex, "severity": target_severity, "msg": uuid.uuid4().hex},
        ]

        filtered = self.audit_log.filter_by_severity(test_dataset, target_severity)

        self.assertEqual(len(filtered), 2)
        for item in filtered:
            self.assertEqual(item["severity"], target_severity)

    def test_incident_correlation_engine(self):
        correlation_key = uuid.uuid4().hex
        incident_stream = [
            {"correlation_id": correlation_key, "step": 1, "data": uuid.uuid4().hex},
            {"correlation_id": uuid.uuid4().hex, "step": 1, "data": uuid.uuid4().hex},
            {"correlation_id": correlation_key, "step": 2, "data": uuid.uuid4().hex},
        ]

        correlated = self.audit_log.correlate_incidents(incident_stream, correlation_key)

        self.assertIsInstance(correlated, list)
        self.assertEqual(len(correlated), 2)
        for incident in correlated:
            self.assertEqual(incident["correlation_id"], correlation_key)

    def test_audit_integrity_hash_verification(self):
        random_payload = uuid.uuid4().bytes + uuid.uuid4().bytes
        mock_hash_algo = random.choice(["sha256", "sha512", "md5"])

        with patch("skills.system_security_audit_log.hashlib") as mock_hashlib:
            mock_hasher = MagicMock()
            expected_digest = uuid.uuid4().hex
            mock_hasher.hexdigest.return_value = expected_digest
            getattr(mock_hashlib, mock_hash_algo).return_value = mock_hasher

            computed_hash = self.audit_log.verify_log_integrity(
                io.BytesIO(random_payload),
                algorithm=mock_hash_algo
            )

        self.assertEqual(computed_hash, expected_digest)
        mock_hasher.update.assert_called()