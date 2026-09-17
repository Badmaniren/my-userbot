import unittest
import uuid
import random
import json
import os
import time
from skills.telemetry_processor import TelemetryProcessor, process_telemetry_packet, incident_aggregator

class TelemetryIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.processor = TelemetryProcessor()
        self.temp_files = []

    def tearDown(self):
        for f in self.temp_files:
            if os.path.exists(f):
                os.remove(f)

    def test_file_ingestion_integration(self):
        # Generate random data to ensure no hardcoded values pass
        random_id = str(uuid.uuid4())
        random_metric = f"sensor_{uuid.uuid4().hex[:8]}"
        random_value = round(random.uniform(10.0, 500.0), 4)
        random_ts = int(time.time()) - random.randint(100, 1000)

        raw_data = {
            "packet_id": random_id,
            "metric_name": random_metric,
            "data_value": random_value,
            "timestamp": random_ts
        }

        filename = f"test_telemetry_{uuid.uuid4().hex}.json"
        self.temp_files.append(filename)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f)

        # Verify file existence as a real system change
        self.assertTrue(os.path.exists(filename))

        # Process via file ingestion
        result = self.processor.ingest_from_file(filename)

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], random_id)
        self.assertEqual(result["metric"], random_metric)
        self.assertEqual(result["value"], float(random_value))
        self.assertEqual(result["timestamp"], random_ts)
        self.assertIn("processed_at", result)

    def test_incident_dispatch_threshold_integration(self):
        # Test interaction with incident_aggregator (no mocks)
        high_value = 1000.01 + random.random()
        packet_id = str(uuid.uuid4())
        
        packet = {
            "packet_id": packet_id,
            "metric_name": "voltage_spike",
            "data_value": high_value,
            "timestamp": int(time.time())
        }

        # This calls incident_aggregator.register_incident internally
        # In a full integration environment, we would check the state of the aggregator
        # or the side effects (logs/db). Here we verify the flow completes.
        processed = self.processor.process_and_dispatch(packet)
        
        self.assertIsNotNone(processed)
        self.assertEqual(processed["id"], packet_id)
        self.assertEqual(processed["value"], high_value)

    def test_hardware_telemetry_pipeline_logic(self):
        # Test the standalone hardware-level function
        sensor_uuid = str(uuid.uuid4())
        raw_val = 42.789123
        session_id = f"session_{uuid.uuid4().hex}"
        ts = int(time.time())

        hw_packet = {
            "sensor_id": sensor_uuid,
            "raw_value": raw_val,
            "unix_timestamp": ts,
            "metadata": {"session": session_id}
        }

        result = process_telemetry_packet(hw_packet)

        self.assertIsNotNone(result)
        self.assertEqual(result["device_uuid"], sensor_uuid)
        # Verify rounding requirement (2 decimal places)
        self.assertEqual(result["metric_value"], 42.79)
        self.assertEqual(result["normalized_timestamp"], ts)
        self.assertEqual(result["origin_session"], session_id)

    def test_batch_processing_consistency(self):
        batch_size = random.randint(3, 7)
        packets = []
        expected_ids = []

        for _ in range(batch_size):
            uid = str(uuid.uuid4())
            expected_ids.append(uid)
            packets.append({
                "packet_id": uid,
                "metric_name": "batch_metric",
                "data_value": random.random(),
                "timestamp": int(time.time())
            })

        # Add one invalid packet to test filtering
        packets.append({"invalid": "data"})

        results = self.processor.process_batch(packets)

        self.assertEqual(len(results), batch_size)
        processed_ids = [r["id"] for r in results]
        for eid in expected_ids:
            self.assertIn(eid, processed_ids)

if __name__ == "__main__":
    unittest.main()