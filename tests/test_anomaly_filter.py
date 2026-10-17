import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.anomaly_filter import start_new


class TestAnomalyFilter(unittest.TestCase):

    def setUp(self):
        self.random_source = uuid.uuid4().hex
        self.random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.random_details = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        self.random_telemetry = {
            "cpu_usage": round(random.uniform(0.0, 100.0), 2),
            "memory_free": random.randint(1024, 65536),
            "node_id": uuid.uuid4().hex
        }

    def test_start_new_success_normalization(self):
        raw_input_data = {
            "source": self.random_source,
            "severity": self.random_severity,
            "details": self.random_details,
            "telemetry_snapshot": self.random_telemetry
        }

        result = start_new(raw_input_data)

        self.assertIsInstance(result, dict)
        self.assertIn("normalized", result)
        self.assertTrue(result["normalized"])
        self.assertEqual(result["source"], self.random_source)
        self.assertEqual(result["severity"], self.random_severity)
        self.assertEqual(result["details"], self.random_details)
        self.assertEqual(result["telemetry_snapshot"], self.random_telemetry)

    def test_start_new_filters_invalid_severity(self):
        invalid_severity = uuid.uuid4().hex.upper()
        raw_input_data = {
            "source": self.random_source,
            "severity": invalid_severity,
            "details": self.random_details,
            "telemetry_snapshot": self.random_telemetry
        }

        result = start_new(raw_input_data)

        self.assertIsInstance(result, dict)
        self.assertIn("normalized", result)
        self.assertFalse(result["normalized"])
        self.assertEqual(result["severity"], "UNKNOWN")

    def test_start_new_with_stream_data(self):
        stream_content = f"{self.random_source}:{self.random_severity}:{self.random_details}".encode('utf-8')
        mock_stream = io.BytesIO(stream_content)

        with patch("skills.anomaly_filter.open", return_value=mock_stream, create=True):
            file_path = f"/var/log/{uuid.uuid4().hex}.log"
            result = start_new(file_path)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("source"), self.random_source)
            self.assertEqual(result.get("severity"), self.random_severity)
            self.assertIn(self.random_details, result.get("details", ""))

    def test_start_new_handles_malformed_input(self):
        malformed_data = {
            "bad_key": uuid.uuid4().hex,
            "corrupted_value": random.randint(1, 1000)
        }

        with self.assertRaises(Exception):
            start_new(malformed_data)

    def test_start_new_empty_telemetry(self):
        raw_input_data = {
            "source": self.random_source,
            "severity": self.random_severity,
            "details": self.random_details,
            "telemetry_snapshot": {}
        }

        result = start_new(raw_input_data)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["telemetry_snapshot"], {})
        self.assertTrue(result["normalized"])


if __name__ == "__main__":
    unittest.main()