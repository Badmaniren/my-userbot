import unittest
import uuid
import random
import os
import json
from skills.telemetry_streamer import TelemetryStreamer
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector
from skills.system_health_aggregator import SystemHealthAggregator
from skills.system_health_audit_pipeline import SystemHealthAuditPipeline

class TestTelemetryStreamerIntegration(unittest.TestCase):
    def setUp(self):
        self.streamer = TelemetryStreamer()
        self.collector = SystemHealthTelemetryCollector()
        self.aggregator = SystemHealthAggregator()
        self.pipeline = SystemHealthAuditPipeline()
        self.test_run_id = str(uuid.uuid4())
        self.temp_log_path = f"audit_{self.test_run_id}.log"

    def tearDown(self):
        if os.path.exists(self.temp_log_path):
            os.remove(self.temp_log_path)

    def test_end_to_end_telemetry_flow(self):
        # 1. Generate random telemetry payload
        raw_data = {
            "node_id": str(uuid.uuid4()),
            "cpu_load": random.uniform(0.0, 100.0),
            "mem_usage": random.uniform(1024, 65536),
            "timestamp": self.test_run_id
        }

        # 2. Collect via real collector
        collected_packet = self.collector.capture(raw_data)
        
        # 3. Stream via TelemetryStreamer (The Module Under Test)
        # We verify the streamer processes the packet and pushes to the pipeline
        stream_result = self.streamer.process_and_push(collected_packet)
        
        self.assertTrue(stream_result.get("success"), "Streamer failed to process packet")
        self.assertEqual(stream_result.get("correlation_id"), self.test_run_id)

        # 4. Aggregate via real aggregator
        aggregated_data = self.aggregator.aggregate([collected_packet])
        
        # 5. Verify persistence in audit pipeline
        pipeline_status = self.pipeline.log_to_audit(aggregated_data, self.temp_log_path)
        
        self.assertTrue(pipeline_status, "Audit pipeline failed to write telemetry")
        self.assertTrue(os.path.exists(self.temp_log_path))

        # 6. Validate data integrity
        with open(self.temp_log_path, 'r') as f:
            content = json.load(f)
            self.assertEqual(content['timestamp'], self.test_run_id)
            self.assertEqual(content['node_id'], raw_data['node_id'])

if __name__ == '__main__':
    unittest.main()