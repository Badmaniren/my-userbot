import unittest
from unittest.mock import patch, MagicMock
import os
import json
import uuid
import random
import string
from skills.anomaly_logger import AnomalyLogger
from skills.system_telemetry import SystemTelemetryError


class TestAnomalyLoggerInquisition(unittest.TestCase):
    def setUp(self):
        self.log_filename = f"test_logs_{uuid.uuid4().hex}.jsonl"
        self.logger = AnomalyLogger(self.log_filename)
        self.random_source = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_severity = random.choice(["INFO", "WARNING", "CRITICAL", "ERROR"])
        self.random_key = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.random_value = ''.join(random.choices(string.ascii_letters, k=12))

    def tearDown(self):
        self.logger.clear_logs()

    @patch("skills.anomaly_logger.SystemTelemetry")
    def test_log_anomaly_writes_valid_json(self, mock_telemetry_class):
        mock_telemetry_instance = MagicMock()
        mock_telemetry_class.return_value = mock_telemetry_instance

        details_dict = {self.random_key: self.random_value}
        
        self.logger.log_anomaly(
            source=self.random_source,
            severity=self.random_severity,
            details=details_dict
        )

        report = self.logger.get_structured_report()
        self.assertTrue(len(report) > 0)
        
        last_entry = report[-1]
        self.assertEqual(last_entry["source"], self.random_source)
        self.assertEqual(last_entry["severity"], self.random_severity)
        self.assertEqual(last_entry["details"][self.random_key], self.random_value)
        self.assertIn("id", last_entry)

    @patch("skills.anomaly_logger.SystemTelemetry")
    def test_telemetry_integration_error_handling(self, mock_telemetry_class):
        mock_telemetry_instance = MagicMock()
        mock_telemetry_instance.send.side_effect = SystemTelemetryError(uuid.uuid4().hex)
        mock_telemetry_class.return_value = mock_telemetry_instance

        details_dict = {self.random_key: self.random_value}

        try:
            self.logger.log_anomaly(
                source=self.random_source,
                severity=self.random_severity,
                details=details_dict
            )
        except Exception as e:
            self.fail(f"AnomalyLogger crashed when SystemTelemetry failed: {e}")

        report = self.logger.get_structured_report()
        self.assertEqual(len(report), 1)
        self.assertEqual(report[0]["source"], self.random_source)

    @patch("skills.anomaly_logger.SystemTelemetry")
    def test_log_anomaly_with_dict_source(self, mock_telemetry_class):
        mock_telemetry_instance = MagicMock()
        mock_telemetry_class.return_value = mock_telemetry_instance

        anomaly_dict = {
            "id": uuid.uuid4().hex,
            "source": self.random_source,
            "severity": self.random_severity,
            "details": {self.random_key: self.random_value}
        }

        self.logger.log_anomaly(anomaly_dict)

        report = self.logger.get_structured_report()
        self.assertEqual(len(report), 1)
        self.assertEqual(report[0]["id"], anomaly_dict["id"])
        self.assertEqual(report[0]["source"], self.random_source)
        self.assertEqual(report[0]["severity"], self.random_severity)

    @patch("skills.anomaly_logger.SystemTelemetry")
    def test_concurrent_write_simulation(self, mock_telemetry_class):
        mock_telemetry_instance = MagicMock()
        mock_telemetry_class.return_value = mock_telemetry_instance

        details_dict = {self.random_key: self.random_value}

        original_open = open

        def mock_open_permission_error(*args, **kwargs):
            if 'a' in kwargs.get('mode', args[1] if len(args) > 1 else ''):
                raise PermissionError(uuid.uuid4().hex)
            return original_open(*args, **kwargs)

        with patch("builtins.open", side_effect=mock_open_permission_error):
            with self.assertRaises(PermissionError):
                self.logger.log_anomaly(
                    source=self.random_source,
                    severity=self.random_severity,
                    details=details_dict
                )

    def test_empty_source_and_details_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.logger.log_anomaly(source="", details={}, severity="")

    @patch("skills.anomaly_logger.SystemTelemetry")
    def test_get_structured_report_handles_corrupted_json(self, mock_telemetry_class):
        mock_telemetry_instance = MagicMock()
        mock_telemetry_class.return_value = mock_telemetry_instance

        valid_anomaly = {
            "id": uuid.uuid4().hex,
            "source": self.random_source,
            "severity": self.random_severity,
            "details": {self.random_key: self.random_value}
        }

        with open(self.log_filename, 'w', encoding='utf-8') as f:
            f.write(json.dumps(valid_anomaly) + '\n')
            f.write("CORRUPTED_JSON_LINE_" + uuid.uuid4().hex + '\n')

        report = self.logger.get_structured_report()
        self.assertEqual(len(report), 1)
        self.assertEqual(report[0]["id"], valid_anomaly["id"])

    @patch("skills.anomaly_logger.SystemTelemetry")
    def test_clear_logs_removes_file(self, mock_telemetry_class):
        mock_telemetry_instance = MagicMock()
        mock_telemetry_class.return_value = mock_telemetry_instance

        self.logger.log_anomaly(
            source=self.random_source,
            severity=self.random_severity,
            details={self.random_key: self.random_value}
        )

        self.assertTrue(os.path.exists(self.log_filename))
        self.logger.clear_logs()
        self.assertFalse(os.path.exists(self.log_filename))


if __name__ == '__main__':
    unittest.main()