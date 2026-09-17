import unittest
import uuid
import random
import time
import os
from skills.telemetry_processor import process_telemetry_packet
from skills.system_health_telemetry_collector import collect_current_metrics
from skills.telemetry_streamer import push_to_pipeline

class TestTelemetryProcessorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_session_id = str(uuid.uuid4())
        self.temp_log = f"telemetry_audit_{self.test_session_id}.log"

    def tearDown(self):
        if os.path.exists(self.temp_log):
            os.remove(self.temp_log)

    def test_full_telemetry_normalization_and_streaming_flow(self):
        # Step 1: Generate random raw data using collector
        # Simulating raw hardware noise and inconsistent naming
        raw_payload = collect_current_metrics()
        
        # Inject random identifiers to ensure no hardcoded bypass
        random_device_id = f"DEV-{uuid.uuid4().hex[:8].upper()}"
        random_cpu_load = random.uniform(0.1, 99.9)
        
        raw_packet = {
            "sensor_id": random_device_id,
            "raw_value": random_cpu_load,
            "unix_timestamp": time.time(),
            "metadata": {
                "session": self.test_session_id,
                "entropy": random.getrandbits(32)
            },
            "source_node": f"node-{random.randint(1, 1000)}"
        }

        # Step 2: Execute the module under test (telemetry_processor)
        # This should filter, normalize keys, and validate against schema
        processed_result = process_telemetry_packet(raw_packet)

        # Step 3: Assertions on normalization logic
        self.assertIsNotNone(processed_result)
        self.assertEqual(processed_result["device_uuid"], random_device_id)
        self.assertIn("normalized_timestamp", processed_result)
        self.assertIsInstance(processed_result["metric_value"], float)
        
        # Check if the processor rounded the float or applied specific schema rules
        # Assuming schema requires 2 decimal places
        expected_value = round(random_cpu_load, 2)
        self.assertEqual(processed_result["metric_value"], expected_value)

        # Step 4: Integration with Telemetry Streamer
        # Passing the processed data to the next skill in the pipeline without mocks
        streaming_response = push_to_pipeline(processed_result)

        # Step 5: Verify real side effects/returns
        # The streamer should return a unique transmission ID and success status
        self.assertTrue(streaming_response.get("status") == "dispatched")
        self.assertIn("transmission_id", streaming_response)
        
        # Verify the transmission ID is a valid UUID (not a stub)
        try:
            uuid.UUID(str(streaming_response["transmission_id"]))
        except ValueError:
            self.fail("telemetry_streamer returned an invalid transmission_id format")

        # Step 6: Verify data consistency across the chain
        # Ensure the session ID survived the processing and streaming
        self.assertEqual(streaming_response["origin_session"], self.test_session_id)

if __name__ == "__main__":
    unittest.main()