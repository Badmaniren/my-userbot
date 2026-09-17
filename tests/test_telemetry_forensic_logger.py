import unittest
from unittest.mock import patch
import io
import uuid
import random
import string
import json
import hashlib
from skills.telemetry_forensic_logger import TelemetryForensicLogger

class TestTelemetryForensicLogger(unittest.TestCase):
    def setUp(self):
        self.logger_instance = TelemetryForensicLogger()
        self.random_anomaly_id = uuid.uuid4().hex
        self.random_telemetry_source = "".join(random.choices(string.ascii_lowercase, k=12))
        self.random_payload_size = random.randint(1024, 65535)
        self.random_raw_bytes = bytes(random.choices(range(256), k=self.random_payload_size))
        self.random_expected_hash = hashlib.sha256(self.random_raw_bytes).hexdigest()

    def test_log_forensic_anomaly_integrity_success(self):
        mock_stream = io.BytesIO(self.random_raw_bytes)

        with patch('skills.telemetry_forensic_logger.open', unittest.mock.mock_open()) as mock_file:
            result = self.logger_instance.log_forensic_data(
                anomaly_id=self.random_anomaly_id,
                source=self.random_telemetry_source,
                data_stream=mock_stream,
                integrity_hash=self.random_expected_hash
            )

            self.assertTrue(result, "Логирование форензик-данных должно завершиться успехом при совпадении хеша.")
            mock_file.assert_called()

    def test_log_forensic_anomaly_integrity_failure(self):
        corrupted_bytes = self.random_raw_bytes[:-10] + bytes(random.choices(range(256), k=10))
        mock_stream = io.BytesIO(corrupted_bytes)

        with patch('skills.telemetry_forensic_logger.open', unittest.mock.mock_open()):
            with self.assertRaises(ValueError):
                self.logger_instance.log_forensic_data(
                    anomaly_id=self.random_anomaly_id,
                    source=self.random_telemetry_source,
                    data_stream=mock_stream,
                    integrity_hash=self.random_expected_hash
                )

    def test_retrieve_forensic_log_entry(self):
        target_id = uuid.uuid4().hex
        mock_record = {
            "anomaly_id": target_id,
            "source": self.random_telemetry_source,
            "checksum": self.random_expected_hash,
            "size": self.random_payload_size
        }
        mock_json_data = json.dumps(mock_record).encode('utf-8')
        mock_stream = io.BytesIO(mock_json_data)

        with patch('skills.telemetry_forensic_logger.open', unittest.mock.mock_open(read_data=mock_json_data)):
            retrieved_data = self.logger_instance.get_forensic_record(target_id)
            self.assertEqual(retrieved_data["anomaly_id"], target_id)
            self.assertEqual(retrieved_data["checksum"], self.random_expected_hash)

    def test_audit_pipeline_integration(self):
        random_event_code = random.randint(1000, 9999)
        audit_payload = {
            "event_id": random_event_code,
            "origin": self.random_telemetry_source,
            "uuid": self.random_anomaly_id
        }

        with patch('requests.post') as mock_requests_post:
            mock_requests_post.return_value.status_code = 200
            mock_requests_post.return_value.json.return_value = {"status": "verified", "code": random_event_code}

            dispatch_result = self.logger_instance.dispatch_to_audit_pipeline(audit_payload)
            self.assertTrue(dispatch_result)
            mock_requests_post.assert_called_once()
            called_args, called_kwargs = mock_requests_post.call_args
            self.assertIn(str(random_event_code), str(called_kwargs))

    def test_forensic_logger_error_recovery_hub(self):
        malformed_stream = io.BytesIO(b"INVALID_STREAM_DATA_" + uuid.uuid4().hex.encode('utf-8'))

        with patch('skills.telemetry_forensic_logger.open', unittest.mock.mock_open()) as mock_file:
            recovery_status = self.logger_instance.handle_stream_failure(
                anomaly_id=self.random_anomaly_id,
                faulty_stream=malformed_stream
            )
            self.assertIsInstance(recovery_status, dict)
            self.assertIn("recovered", recovery_status)
            self.assertEqual(recovery_status.get("anomaly_id"), self.random_anomaly_id)