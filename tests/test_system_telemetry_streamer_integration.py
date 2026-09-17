import unittest
import uuid
import random
import time
from skills.system_telemetry_streamer import system_telemetry_streamer
from skills.system_health_telemetry_collector import system_health_telemetry_collector
from skills.system_health_aggregator import system_health_aggregator

class TestSystemTelemetryStreamerIntegration(unittest.TestCase):
    def test_telemetry_streaming_and_aggregation_real(self):
        unique_metric_id = str(uuid.uuid4())
        random_cpu_load = round(random.uniform(10.0, 99.9), 2)
        random_memory_usage = round(random.uniform(20.0, 95.0), 2)

        raw_telemetry_payload = {
            "metric_id": unique_metric_id,
            "cpu_load": random_cpu_load,
            "memory_usage": random_memory_usage,
            "timestamp": time.time()
        }

        collected_data = system_health_telemetry_collector(raw_telemetry_payload)

        stream_result = system_telemetry_streamer(collected_data)

        aggregated_health = system_health_aggregator(stream_result)

        self.assertIsNotNone(aggregated_health, "Агрегатор не должен возвращать None")
        self.assertIn("metric_id", aggregated_health)
        self.assertEqual(aggregated_health["metric_id"], unique_metric_id, "ID метрики должен совпадать со сгенерированным")

        if "metrics" in aggregated_health:
            self.assertEqual(aggregated_health["metrics"]["cpu_load"], random_cpu_load)
            self.assertEqual(aggregated_health["metrics"]["memory_usage"], random_memory_usage)
        else:
            self.assertEqual(aggregated_health.get("cpu_load"), random_cpu_load)

if __name__ == "__main__":
    unittest.main()