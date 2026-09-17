import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

class TestTelemetryProcessor(unittest.TestCase):
    def setUp(self):
        self.random_id = str(uuid.uuid4())
        self.random_metric = "".join(random.choices(string.ascii_letters, k=15))
        self.random_value = random.uniform(0.0, 10000.0)
        self.random_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.raw"

    def _generate_chaos_packet(self, valid=True):
        if valid:
            return {
                "packet_id": str(uuid.uuid4()),
                "metric_name": "".join(random.choices(string.ascii_uppercase, k=8)),
                "data_value": str(random.uniform(-100, 100)),
                "timestamp": random.randint(1600000000, 1700000000)
            }
        return {
            "garbage_field": uuid.uuid4().hex,
            "noise": random.random()
        }

    def test_normalization_logic_and_schema_mapping(self):
        from skills.telemetry_processor import TelemetryProcessor
        processor = TelemetryProcessor()
        
        test_id = str(uuid.uuid4())
        test_val = random.uniform(1.0, 500.0)
        raw_packet = {
            "packet_id": test_id,
            "metric_name": "system_load",
            "data_value": str(test_val),
            "timestamp": 1672531200
        }

        normalized = processor.process_packet(raw_packet)

        # Assertions check if internal logic correctly maps and casts types
        self.assertEqual(normalized["id"], test_id)
        self.assertIsInstance(normalized["value"], float)
        self.assertEqual(normalized["value"], test_val)
        self.assertTrue(all(k in normalized for k in ["id", "metric", "value", "timestamp", "processed_at"]))

    def test_filter_drops_invalid_schema_packets(self):
        from skills.telemetry_processor import TelemetryProcessor
        processor = TelemetryProcessor()
        
        invalid_packet = self._generate_chaos_packet(valid=False)
        result = processor.process_packet(invalid_packet)
        
        self.assertIsNone(result, "Processor must return None for packets missing mandatory schema fields")

    def test_stream_ingestion_from_raw_bytes(self):
        from skills.telemetry_processor import TelemetryProcessor
        processor = TelemetryProcessor()
        
        expected_id = str(uuid.uuid4())
        raw_json_content = json.dumps({
            "packet_id": expected_id,
            "metric_name": "network_latency",
            "data_value": "42.5",
            "timestamp": random.randint(1000, 9999)
        }).encode('utf-8')
        
        mock_stream = io.BytesIO(raw_json_content)
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value = mock_stream
            
            # Simulate reading from a random file path
            result = processor.ingest_from_file(self.random_path)
            
            self.assertIsNotNone(result)
            self.assertEqual(result["id"], expected_id)

    def test_integration_with_incident_aggregator_on_anomaly(self):
        from skills.telemetry_processor import TelemetryProcessor
        processor = TelemetryProcessor()
        
        # High value to trigger a simulated anomaly
        anomaly_packet = {
            "packet_id": str(uuid.uuid4()),
            "metric_name": "error_count",
            "data_value": "999999.9",
            "timestamp": random.randint(1000, 9999)
        }

        # Testing interaction with the 'incident_aggregator' signature mentioned in requirements
        with patch('skills.telemetry_processor.incident_aggregator') as mock_aggregator:
            processor.process_and_dispatch(anomaly_packet)
            
            # Verify that the aggregator was notified because of the high value
            self.assertTrue(mock_aggregator.register_incident.called)
            call_args = mock_aggregator.register_incident.call_args[0][0]
            self.assertEqual(call_args["id"], anomaly_packet["packet_id"])

    def test_batch_processing_chaos_resilience(self):
        from skills.telemetry_processor import TelemetryProcessor
        processor = TelemetryProcessor()
        
        batch_size = random.randint(5, 15)
        valid_id = str(uuid.uuid4())
        
        # Create a mix of valid and invalid packets
        packets = [self._generate_chaos_packet(valid=False) for _ in range(batch_size)]
        valid_packet = self._generate_chaos_packet(valid=True)
        valid_packet["packet_id"] = valid_id
        packets.append(valid_packet)
        
        random.shuffle(packets)
        
        results = processor.process_batch(packets)
        
        # Ensure only the valid packet survived the filter
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], valid_id)

    def test_normalization_timestamp_consistency(self):
        from skills.telemetry_processor import TelemetryProcessor
        processor = TelemetryProcessor()
        
        # Test with a string timestamp that should be normalized to integer
        ts_val = random.randint(1000000, 2000000)
        packet = {
            "packet_id": str(uuid.uuid4()),
            "metric_name": "cpu_usage",
            "data_value": "15.0",
            "timestamp": str(ts_val)
        }
        
        normalized = processor.process_packet(packet)
        self.assertIsInstance(normalized["timestamp"], int)
        self.assertEqual(normalized["timestamp"], ts_val)

if __name__ == '__main__':
    unittest.main()