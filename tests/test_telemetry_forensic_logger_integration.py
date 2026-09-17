import unittest
import uuid
import random
import os
import tempfile
from skills.telemetry_forensic_logger import telemetry_forensic_logger
from skills.telemetry_processor import telemetry_processor
from skills.telemetry_streamer import telemetry_streamer
from skills.system_health_telemetry_collector import system_health_telemetry_collector
from skills.incident_aggregator import incident_aggregator

class TestTelemetryForensicLoggerIntegration(unittest.TestCase):
    def test_forensic_logger_integration_end_to_end(self):
        unique_anomaly_id = str(uuid.uuid4())
        metric_value = random.uniform(100.0, 999.9)
        raw_payload = {
            "anomaly_id": unique_anomaly_id,
            "metric": metric_value,
            "source": "integration_test_node",
            "status": "CRITICAL"
        }

        streamer_result = telemetry_streamer(raw_payload)
        self.assertIsNotNone(streamer_result)

        processed_data = telemetry_processor(raw_payload)
        self.assertIsInstance(processed_data, dict)

        health_data = system_health_telemetry_collector(processed_data)
        self.assertIsNotNone(health_data)

        incident_record = incident_aggregator({
            "id": unique_anomaly_id,
            "health": health_data,
            "payload": raw_payload
        })
        self.assertIsNotNone(incident_record)

        with tempfile.TemporaryDirectory() as temp_dir:
            log_filepath = os.path.join(temp_dir, f"forensic_{unique_anomaly_id}.log")

            forensic_output = telemetry_forensic_logger(
                incident_data=incident_record,
                output_path=log_filepath,
                verify_integrity=True
            )

            self.assertTrue(os.path.exists(log_filepath), "Форензик-лог файл не был создан.")

            with open(log_filepath, "r", encoding="utf-8") as f:
                log_content = f.read()

            self.assertIn(unique_anomaly_id, log_content, "Случайный UUID аномалии не найден в лог-файле.")
            self.assertIn(str(metric_value), log_content, "Значение метрики не зафиксировано в форензик-логе.")
            self.assertIsInstance(forensic_output, dict)
            self.assertIn("checksum", forensic_output)

if __name__ == "__main__":
    unittest.main()