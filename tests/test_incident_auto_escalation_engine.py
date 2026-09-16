import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.incident_auto_escalation_engine import (
    IncidentAutoEscalationEngine,
    EscalationConfigurationError,
    ExternalAggregatorConnectionError
)


class TestIncidentAutoEscalationEngine(unittest.TestCase):

    def setUp(self):
        self.engine_id = uuid.uuid4().hex
        self.severity_evaluator = MagicMock()
        self.incident_aggregator = MagicMock()
        self.notification_bridge = MagicMock()

        self.engine = IncidentAutoEscalationEngine(
            engine_id=self.engine_id,
            severity_evaluator=self.severity_evaluator,
            incident_aggregator=self.incident_aggregator,
            notification_bridge=self.notification_bridge
        )

    def test_evaluate_and_escalate_incident_critical_success(self):
        incident_id = uuid.uuid4().hex
        raw_log_data = ''.join(random.choices(string.ascii_letters + string.digits, k=64))
        calculated_severity = random.choice(["CRITICAL", "FATAL", "EMERGENCY"])
        aggregator_ticket_id = uuid.uuid4().hex

        self.severity_evaluator.evaluate.return_value = calculated_severity
        self.incident_aggregator.create_ticket.return_value = aggregator_ticket_id

        with patch('skills.incident_auto_escalation_engine.requests.post') as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {"status": "escalated", "ticket": aggregator_ticket_id}

            result = self.engine.process_incident(incident_id, raw_log_data)

            self.assertEqual(result["incident_id"], incident_id)
            self.assertEqual(result["severity"], calculated_severity)
            self.assertEqual(result["ticket_id"], aggregator_ticket_id)
            self.assertTrue(result["escalated"])

            self.severity_evaluator.evaluate.assert_called_once_with(raw_log_data)
            self.incident_aggregator.create_ticket.assert_called_once()
            self.notification_bridge.dispatch.assert_called_once()

    def test_evaluate_and_escalate_incident_low_severity_ignored(self):
        incident_id = uuid.uuid4().hex
        raw_log_data = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        calculated_severity = random.choice(["LOW", "DEBUG", "INFO", "WARNING"])

        self.severity_evaluator.evaluate.return_value = calculated_severity

        result = self.engine.process_incident(incident_id, raw_log_data)

        self.assertEqual(result["incident_id"], incident_id)
        self.assertEqual(result["severity"], calculated_severity)
        self.assertFalse(result["escalated"])
        self.assertIsNone(result.get("ticket_id"))

        self.severity_evaluator.evaluate.assert_called_once_with(raw_log_data)
        self.incident_aggregator.create_ticket.assert_not_called()
        self.notification_bridge.dispatch.assert_not_called()

    def test_escalation_with_io_stream_payload(self):
        incident_id = uuid.uuid4().hex
        random_bytes = ''.join(random.choices(string.ascii_letters, k=128)).encode('utf-8')
        stream_payload = io.BytesIO(random_bytes)
        calculated_severity = "CRITICAL"
        aggregator_ticket_id = uuid.uuid4().hex

        self.severity_evaluator.evaluate_stream.return_value = calculated_severity
        self.incident_aggregator.create_ticket.return_value = aggregator_ticket_id

        result = self.engine.process_stream_incident(incident_id, stream_payload)

        self.assertEqual(result["incident_id"], incident_id)
        self.assertTrue(result["escalated"])
        self.assertEqual(result["ticket_id"], aggregator_ticket_id)
        self.severity_evaluator.evaluate_stream.assert_called_once_with(stream_payload)

    def test_aggregator_connection_failure_raises_custom_exception(self):
        incident_id = uuid.uuid4().hex
        raw_log_data = ''.join(random.choices(string.ascii_letters, k=40))
        self.severity_evaluator.evaluate.return_value = "CRITICAL"
        self.incident_aggregator.create_ticket.side_effect = ConnectionError(uuid.uuid4().hex)

        with self.assertRaises(ExternalAggregatorConnectionError):
            self.engine.process_incident(incident_id, raw_log_data)

        self.notification_bridge.dispatch_alert.assert_not_called()

    def test_configuration_error_missing_evaluator(self):
        with self.assertRaises(EscalationConfigurationError):
            IncidentAutoEscalationEngine(
                engine_id=uuid.uuid4().hex,
                severity_evaluator=None,
                incident_aggregator=self.incident_aggregator,
                notification_bridge=self.notification_bridge
            )

    def test_batch_incident_processing(self):
        batch_size = random.randint(3, 7)
        incidents = []
        for _ in range(batch_size):
            inc_id = uuid.uuid4().hex
            log_data = uuid.uuid4().hex
            sev = random.choice(["CRITICAL", "LOW"])
            incidents.append({"id": inc_id, "log": log_data, "severity": sev})

        def mock_eval(log):
            for i in incidents:
                if i["log"] == log:
                    return i["severity"]
            return "LOW"

        self.severity_evaluator.evaluate.side_effect = mock_eval
        self.incident_aggregator.create_ticket.return_value = uuid.uuid4().hex

        results = self.engine.process_batch(incidents)

        self.assertEqual(len(results), batch_size)
        for res in results:
            matching = next(i for i in incidents if i["id"] == res["incident_id"])
            if matching["severity"] == "CRITICAL":
                self.assertTrue(res["escalated"])
            else:
                self.assertFalse(res["escalated"])