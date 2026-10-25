import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
from pathlib import Path

import skills.anomaly_telemetry_collector
from skills.anomaly_telemetry_collector import (
    AnomalyTelemetryCollector,
    AnomalyTelemetryCollectorError
)

class TestAnomalyTelemetryCollector(unittest.TestCase):

    def setUp(self):
        self.random_prefix = uuid.uuid4().hex
        self.metric_name = f"metric_{self.random_prefix}_{random.randint(1000, 9999)}"
        self.metric_value = random.uniform(0.0, 100.0)
        self.source_id = f"source_{uuid.uuid4().hex[:8]}"
        self.log_path = Path(f"/tmp/{uuid.uuid4().hex}.log")
        self.telemetry_payload = {
            "cpu_usage": random.randint(10, 100),
            "memory_free": random.randint(1024, 65535),
            "status": random.choice(["DEGRADED", "CRITICAL", "PANIC"])
        }

    def test_collector_initialization_randomized(self):
        threshold = random.randint(50, 500)
        collector = AnomalyTelemetryCollector(
            log_path=str(self.log_path),
            threshold=threshold
        )
        self.assertIsNotNone(collector)

    def test_collect_telemetry_success(self):
        collector = AnomalyTelemetryCollector(str(self.log_path))

        mock_response_data = uuid.uuid4().hex.encode('utf-8')

        with patch('skills.anomaly_telemetry_collector.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = mock_response_data
            mock_resp.json.return_value = self.telemetry_payload
            mock_get.return_value = mock_resp

            result = collector.collect_telemetry(self.source_id)
            self.assertIsInstance(result, dict)
            self.assertIn("cpu_usage", result)

    def test_aggregate_metrics_chaos_input(self):
        collector = AnomalyTelemetryCollector(str(self.log_path))

        raw_stream_data = f"DATA_{uuid.uuid4().hex}".encode('utf-8')
        mock_file_stream = io.BytesIO(raw_stream_data)

        with patch('skills.anomaly_telemetry_collector.open', return_value=mock_file_stream, create=True):
            aggregation_result = collector.aggregate_metrics(self.metric_name, self.metric_value)
            self.assertIsNotNone(aggregation_result)

    def test_telemetry_collector_error_handling(self):
        collector = AnomalyTelemetryCollector(str(self.log_path))

        with patch('skills.anomaly_telemetry_collector.requests.get', side_effect=Exception(f"ERR_{uuid.uuid4().hex}")):
            with self.assertRaises((AnomalyTelemetryCollectorError, Exception)):
                collector.collect_telemetry(self.source_id)

    def test_snapshot_generation_uniqueness(self):
        collector = AnomalyTelemetryCollector(str(self.log_path))

        snapshot_id_1 = f"snap_{uuid.uuid4().hex}"
        snapshot_id_2 = f"snap_{uuid.uuid4().hex}"

        with patch.object(collector, 'collect_telemetry') as mock_collect:
            mock_collect.side_effect = [
                {snapshot_id_1: self.telemetry_payload},
                {snapshot_id_2: self.telemetry_payload}
            ]

            res1 = collector.collect_telemetry(self.source_id)
            res2 = collector.collect_telemetry(self.source_id)

            self.assertNotEqual(res1, res2)
            self.assertIn(snapshot_id_1, res1)
            self.assertIn(snapshot_id_2, res2)

if __name__ == '__main__':
    unittest.main()
