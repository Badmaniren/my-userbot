import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
from skills.incident_forensic_analyzer import start_new

class TestIncidentForensicAnalyzer(unittest.TestCase):

    def setUp(self):
        self.random_incident_id = uuid.uuid4().hex
        self.random_telemetry_source = f"source_{uuid.uuid4().hex[:8]}"
        self.random_log_path = f"/var/log/{uuid.uuid4().hex}.log"
        self.random_error_code = random.randint(1000, 9999)
        self.random_payload = ''.join(random.choices(string.ascii_letters + string.digits, k=64))

    def test_start_new_success_execution(self):
        config_data = {
            "incident_id": self.random_incident_id,
            "telemetry_source": self.random_telemetry_source,
            "log_path": self.random_log_path,
            "error_code": self.random_error_code
        }

        mock_telemetry_streamer = MagicMock()
        mock_telemetry_streamer.read.return_value = self.random_payload.encode('utf-8')

        with patch("skills.incident_forensic_analyzer.telemetry_streamer", return_value=mock_telemetry_streamer), \
             patch("skills.incident_forensic_analyzer.incident_aggregator") as mock_aggregator:
            
            mock_aggregator.process.return_value = True
            
            result = start_new(config_data)
            
            self.assertIsNotNone(result)
            self.assertIn(self.random_incident_id, str(result))
            mock_aggregator.process.assert_called_once()

    def test_start_new_with_malformed_telemetry(self):
        bad_config = {
            "incident_id": self.random_incident_id,
            "corrupted_stream": True
        }

        mock_stream = io.BytesIO(b"")

        with patch("skills.incident_forensic_analyzer.telemetry_streamer", return_value=mock_stream), \
             patch("skills.incident_forensic_analyzer.error_recovery_hub") as mock_recovery:
            
            mock_recovery.handle_failure.return_value = f"recovered_{self.random_incident_id}"

            result = start_new(bad_config)

            self.assertIn(self.random_incident_id, str(result))
            mock_recovery.handle_failure.assert_called_once()

    def test_start_new_impact_evaluation(self):
        evaluation_config = {
            "incident_id": self.random_incident_id,
            "severity_level": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "financial_index": random.uniform(100.5, 99999.9)
        }

        mock_evaluator = MagicMock()
        mock_evaluator.evaluate.return_value = {
            "status": "analyzed",
            "impact_id": self.random_incident_id
        }

        with patch("skills.incident_forensic_analyzer.incident_severity_evaluator", mock_evaluator):
            result = start_new(evaluation_config)

            self.assertEqual(result.get("impact_id"), self.random_incident_id)
            mock_evaluator.evaluate.assert_called_once()

    def test_start_new_anomaly_detection_trigger(self):
        anomaly_config = {
            "incident_id": self.random_incident_id,
            "anomaly_signature": self.random_payload
        }

        with patch("skills.incident_forensic_analyzer.telemetry_anomaly_evaluator_core") as mock_anomaly_core:
            mock_anomaly_core.detect.return_value = {
                "anomaly_detected": True,
                "target_id": self.random_incident_id
            }

            result = start_new(anomaly_config)

            self.assertTrue(result.get("anomaly_detected"))
            self.assertEqual(result.get("target_id"), self.random_incident_id)
            mock_anomaly_core.detect.assert_called_once()

    def test_start_new_empty_payload_handling(self):
        empty_config = {}

        with patch("skills.incident_forensic_analyzer.system_health_telemetry_collector") as mock_collector:
            mock_collector.collect.side_effect = Exception("Telemetry failure")

            with self.assertRaises(Exception):
                start_new(empty_config)

            mock_collector.collect.assert_called_once()

if __name__ == "__main__":
    unittest.main()