import unittest
import uuid
import random
import io
from skills.telemetry_anomaly_response_connector import (
    TelemetryAnomalyResponseConnector,
    ConnectorException,
    connect_telemetry_to_escalation
)
from skills.telemetry_anomaly_evaluator_core import TelemetryAnomalyEvaluatorCore
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine


class TestTelemetryAnomalyResponseConnectorIntegration(unittest.TestCase):

    def setUp(self):
        self.evaluator = TelemetryAnomalyEvaluatorCore()
        self.escalation_engine = IncidentAutoEscalationEngine()
        self.connector = TelemetryAnomalyResponseConnector(
            evaluator=self.evaluator,
            escalation_engine=self.escalation_engine
        )

    def test_handle_telemetry_and_respond_integration(self):
        random_id = str(uuid.uuid4())
        metric_value = random.uniform(100.0, 1000.0)
        
        telemetry_payload = {
            "incident_id": random_id,
            "metric_value": metric_value,
            "status": "CRITICAL",
            "source": "integration_test_stream"
        }

        result = self.connector.handle_telemetry_and_respond(telemetry_payload)

        self.assertIn("anomaly_handled", result)
        self.assertIn("evaluation", result)
        self.assertIn("escalation", result)
        
        self.assertTrue(result["anomaly_handled"])
        self.assertEqual(result["evaluation"].get("incident_id"), random_id)

    def test_invalid_telemetry_stream_fallback_integration(self):
        random_id = str(uuid.uuid4())
        # Передаем некорректную структуру, чтобы спровоцировать InvalidTelemetryStreamException и fallback
        telemetry_payload = {
            "incident_id": random_id,
            "corrupted_field": random.randint(1, 100)
        }

        result = self.connector.handle_telemetry_and_respond(telemetry_payload)

        self.assertTrue(result["anomaly_handled"])
        self.assertEqual(result["evaluation"]["incident_id"], random_id)
        self.assertIn("Forced fallback evaluation", result["evaluation"]["details"])

    def test_process_telemetry_stream_integration(self):
        random_id = str(uuid.uuid4())
        stream_content = f'{{"incident_id": "{random_id}", "metric": {random.randint(50, 500)}}}'.encode('utf-8')
        stream_io = io.BytesIO(stream_content)

        result = self.connector.process_telemetry_stream(stream_io)

        self.assertIn("stream_result", result)
        self.assertIn("escalation_result", result)

    def test_evaluate_and_mitigate_risks_integration(self):
        result = self.connector.evaluate_and_mitigate_risks()

        self.assertIn("risk_assessment", result)
        self.assertIn("patch_triggered", result)
        self.assertIsInstance(result["patch_triggered"], bool)

    def test_process_incoming_stream_integration(self):
        random_id = str(uuid.uuid4())
        raw_data = f'{{"incident_id": "{random_id}", "status": "WARNING"}}'.encode('utf-8')

        result = self.connector.process_incoming_stream(raw_data)
        
        self.assertIsInstance(result, dict)

    def test_verify_and_trigger_response_integration(self):
        response = self.connector.verify_and_trigger_response()
        self.assertIsInstance(response, bool)

    def test_connect_telemetry_to_escalation_helper_integration(self):
        random_id = str(uuid.uuid4())
        payload = {
            "incident_id": random_id,
            "metric_value": random.randint(1, 1000)
        }

        result = connect_telemetry_to_escalation(payload)

        self.assertIsInstance(result, dict)
        self.assertIn("anomaly_handled", result)


if __name__ == "__main__":
    unittest.main()