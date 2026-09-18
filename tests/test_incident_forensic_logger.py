import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

try:
    from skills.incident_forensic_logger import start_new
except ImportError:
    incident_forensic_logger = types.ModuleType("skills.incident_forensic_logger")
    incident_forensic_logger.start_new = lambda *args, **kwargs: None
    sys.modules["skills.incident_forensic_logger"] = incident_forensic_logger
    from skills.incident_forensic_logger import start_new


class TestIncidentForensicLoggerArchitect(unittest.TestCase):

    def setUp(self):
        self.random_incident_id = uuid.uuid4().hex
        self.random_telemetry_source = ''.join(random.choices(string.ascii_lowercase, k=12))
        self.random_payload = uuid.uuid4().bytes + ''.join(random.choices(string.printable, k=64)).encode('utf-8')
        self.random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL", uuid.uuid4().hex[:6]])
        self.random_path = f"/var/log/security/{uuid.uuid4().hex}/{random.choice(string.ascii_lowercase)}.log"

    def test_start_new_executes_with_valid_telemetry_stream(self):
        mock_stream = io.BytesIO(self.random_payload)
        
        with patch('skills.incident_forensic_logger.telemetry_streamer') as mock_streamer, \
             patch('skills.incident_forensic_logger.incident_aggregator') as mock_aggregator:
            
            mock_streamer.return_value = mock_stream
            mock_aggregator.aggregate.return_value = self.random_incident_id

            result = start_new(
                incident_id=self.random_incident_id,
                source=self.random_telemetry_source,
                stream=mock_stream,
                severity=self.random_severity
            )

            mock_streamer.assert_called()
            self.assertIsNotNone(result)

    def test_start_new_handles_anomalous_telemetry_payload(self):
        chaotic_bytes = bytearray(random.getrandbits(8) for _ in range(128))
        mock_reader = io.BytesIO(bytes(chaotic_bytes))

        with patch('skills.incident_forensic_logger.telemetry_anomaly_evaluator_core') as mock_evaluator:
            mock_evaluator.evaluate.return_value = {
                "anomaly_detected": True,
                "score": random.uniform(0.1, 99.9),
                "token": self.random_incident_id
            }

            try:
                response = start_new(
                    incident_id=self.random_incident_id,
                    telemetry_data=mock_reader,
                    mode=self.random_severity
                )
            except Exception as e:
                self.fail(f"start_new crashed on chaotic telemetry payload: {e}")

    def test_start_new_integrates_with_system_health_telemetry(self):
        random_metric_key = uuid.uuid4().hex
        random_metric_value = random.randint(100, 99999)

        with patch('skills.incident_forensic_logger.system_health_telemetry_collector') as mock_collector:
            mock_collector.collect.return_value = {
                random_metric_key: random_metric_value,
                "incident_ref": self.random_incident_id
            }

            res = start_new(
                target_id=self.random_incident_id,
                telemetry_channel=self.random_telemetry_source
            )

            mock_collector.collect.assert_called()

    def test_start_new_triggers_incident_notification_bridge(self):
        random_webhook_url = f"https://security.{uuid.uuid4().hex}.internal/webhook"

        with patch('skills.incident_forensic_logger.incident_notification_bridge') as mock_bridge:
            mock_bridge.dispatch.return_value = status_code := random.choice([200, 201, 202])

            output = start_new(
                incident_id=self.random_incident_id,
                bridge_target=random_webhook_url,
                severity=self.random_severity
            )

            mock_bridge.dispatch.assert_called()

    def test_start_new_verifies_forensic_integrity_via_extractor(self):
        random_artifact = ''.join(random.choices(string.hexdigits, k=32))

        with patch(f'skills.incident_forensic_logger.extractor_tool_1789544538') as mock_extractor:
            mock_extractor.extract.return_value = {
                "artifact_hash": random_artifact,
                "status": "VERIFIED"
            }

            execution_output = start_new(
                incident_id=self.random_incident_id,
                artifact_path=self.random_path
            )

            mock_extractor.extract.assert_called()


if __name__ == '__main__':
    unittest.main()