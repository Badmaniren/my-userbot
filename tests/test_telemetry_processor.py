import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
import uuid
import random
import time
import io

# Assuming the module is located at skills/telemetry_processor.py
from skills.telemetry_processor import TelemetryProcessor, process_telemetry_packet, IncidentAggregator

class TestTelemetryProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = TelemetryProcessor()

    def test_process_packet_success(self):
        """Ensure valid packet is correctly normalized with random data."""
        p_id = uuid.uuid4().hex
        m_name = f"metric_{uuid.uuid4().hex[:6]}"
        val = random.uniform(10.0, 500.0)
        ts = random.randint(1600000000, 1700000000)
        
        raw = {
            "packet_id": p_id,
            "metric_name": m_name,
            "data_value": str(val),
            "timestamp": ts
        }
        
        fixed_now = 123456789.0
        with patch("time.time", return_value=fixed_now):
            result = self.processor.process_packet(raw)
            
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], p_id)
        self.assertEqual(result["metric"], m_name)
        self.assertEqual(result["value"], float(val))
        self.assertEqual(result["timestamp"], ts)
        self.assertEqual(result["processed_at"], fixed_now)

    def test_process_packet_missing_fields(self):
        """Ensure None is returned if mandatory fields are missing."""
        raw = {"packet_id": uuid.uuid4().hex} # Missing others
        self.assertIsNone(self.processor.process_packet(raw))

    def test_process_packet_invalid_types(self):
        """Ensure None is returned on incompatible data types."""
        raw = {
            "packet_id": uuid.uuid4().hex,
            "metric_name": "test",
            "data_value": "not-a-float",
            "timestamp": "not-an-int"
        }
        self.assertIsNone(self.processor.process_packet(raw))

    def test_ingest_from_file(self):
        """Verify file reading and processing logic using random content."""
        random_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        random_id = uuid.uuid4().hex
        mock_data = {
            "packet_id": random_id,
            "metric_name": uuid.uuid4().hex,
            "data_value": random.uniform(1, 100),
            "timestamp": random.randint(1000, 2000)
        }
        
        json_str = json.dumps(mock_data)
        with patch("builtins.open", mock_open(read_data=json_str)):
            # We also need to mock json.load because mock_open read_data 
            # works for .read() but json.load(f) behaves differently in some envs
            with patch("json.load", return_value=mock_data):
                result = self.processor.ingest_from_file(random_path)
                self.assertEqual(result["id"], random_id)

    def test_process_and_dispatch_anomaly(self):
        """Verify incident registration when value > 1000.0."""
        high_val = 1000.01 + random.random()
        raw = {
            "packet_id": uuid.uuid4().hex,
            "metric_name": "voltage",
            "data_value": high_val,
            "timestamp": int(time.time())
        }
        
        with patch("skills.telemetry_processor.incident_aggregator.register_incident") as mock_reg:
            result = self.processor.process_and_dispatch(raw)
            self.assertIsNotNone(result)
            mock_reg.assert_called_once_with(result)

    def test_process_and_dispatch_normal(self):
        """Verify no incident is registered for normal values."""
        low_val = 999.99 - random.random()
        raw = {
            "packet_id": uuid.uuid4().hex,
            "metric_name": "voltage",
            "data_value": low_val,
            "timestamp": int(time.time())
        }
        
        with patch("skills.telemetry_processor.incident_aggregator.register_incident") as mock_reg:
            self.processor.process_and_dispatch(raw)
            mock_reg.assert_not_called()

    def test_process_batch(self):
        """Verify batch processing filters invalid packets."""
        valid_id = uuid.uuid4().hex
        packets = [
            {"packet_id": valid_id, "metric_name": "m1", "data_value": 1.0, "timestamp": 100},
            {"invalid": "packet"},
            {"packet_id": "fail", "metric_name": "m2", "data_value": "bad", "timestamp": 200}
        ]
        
        results = self.processor.process_batch(packets)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], valid_id)

class TestStandaloneTelemetry(unittest.TestCase):
    def test_process_telemetry_packet_rounding(self):
        """Verify rounding to 2 decimal places and metadata preservation."""
        s_id = uuid.uuid4().hex
        raw_val = 123.456789
        session_id = f"sess_{uuid.uuid4().hex}"
        
        raw = {
            "sensor_id": s_id,
            "raw_value": raw_val,
            "unix_timestamp": 1600000000,
            "metadata": {"session": session_id, "other": "data"}
        }
        
        result = process_telemetry_packet(raw)
        self.assertEqual(result["device_uuid"], s_id)
        self.assertEqual(result["metric_value"], 123.46)
        self.assertEqual(result["origin_session"], session_id)

    def test_process_telemetry_packet_no_metadata(self):
        """Verify function works without optional metadata."""
        raw = {
            "sensor_id": uuid.uuid4().hex,
            "raw_value": 50.0,
            "unix_timestamp": 1600000000
        }
        result = process_telemetry_packet(raw)
        self.assertIn("metric_value", result)
        self.assertNotIn("origin_session", result)

    def test_process_telemetry_packet_failure(self):
        """Verify None on missing required hardware fields."""
        raw = {"sensor_id": "only"}
        self.assertIsNone(process_telemetry_packet(raw))

if __name__ == "__main__":
    unittest.main()