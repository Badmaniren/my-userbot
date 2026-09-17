import unittest
import uuid
import random
import os
import json
from skills.telemetry_streamer import (
    TelemetryStreamer,
    StreamAggregationEngine,
    PipelineConnector,
    SystemHealthTelemetryCollector,
    SystemHealthAggregator,
    SystemHealthAuditPipeline
)

class TestTelemetryStreamerIntegration(unittest.TestCase):
    def test_end_to_end_telemetry_pipeline(self):
        random_id = str(uuid.uuid4())
        metric_value = random.randint(100, 9999)

        payload = {
            "timestamp": random_id,
            "metric": metric_value,
            "status": "nominal"
        }

        collector = SystemHealthTelemetryCollector()
        captured_data = collector.capture(payload)

        aggregator = SystemHealthAggregator()
        aggregated_packet = aggregator.aggregate([captured_data])

        self.assertEqual(aggregated_packet.get("timestamp"), random_id)
        self.assertEqual(aggregated_packet.get("metric"), metric_value)

        streamer = TelemetryStreamer(stream_id=random_id)
        process_result = streamer.process_and_push(aggregated_packet)

        self.assertTrue(process_result["success"])
        self.assertEqual(process_result["correlation_id"], random_id)

        audit_filename = f"audit_{random_id}.json"
        audit_pipeline = SystemHealthAuditPipeline()
        audit_written = audit_pipeline.log_to_audit(aggregated_packet, audit_filename)

        self.assertTrue(audit_written)
        self.assertTrue(os.path.exists(audit_filename))

        with open(audit_filename, 'r') as f:
            read_data = json.load(f)

        self.assertEqual(read_data.get("timestamp"), random_id)
        self.assertEqual(read_data.get("metric"), metric_value)

        if os.path.exists(audit_filename):
            os.remove(audit_filename)

if __name__ == '__main__':
    unittest.main()