import unittest
import uuid
import random
from skills.telemetry_anomaly_response_connector import (
    connect_telemetry_to_escalation,
    TelemetryAnomalyResponseConnector
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
        self.random_metric_id = str(uuid.uuid4())
        self.random_cpu_load = round(random.uniform(85.0, 99.9), 2)
        self.random_incident_id = f"INC-{random.randint(10000, 99999)}"

    def test_end_to_end_anomaly_response_composition(self):
        telemetry_payload = {
            "metric_id": self.random_metric_id,
            "cpu_usage": self.random_cpu_load,
            "status": "CRITICAL",
            "incident_id": self.random_incident_id
        }

        result = connect_telemetry_to_escalation(telemetry_payload)

        self.assertIsInstance(result, dict)
        self.assertIn("evaluation", result)
        self.assertIn("escalation", result)
        
        escalation_data = result["escalation"]
        self.assertIsInstance(escalation_data, dict)
        
        risk_evaluation = self.escalation_engine.evaluate_system_telemetry_risks()
        self.assertIsInstance(risk_evaluation, dict)

    def test_connector_class_pipeline(self):
        stream_data = f"stream_metric_{uuid.uuid4()}:{random.randint(500, 1500)}".encode("utf-8")
        
        evaluation_result = self.connector.process_incoming_stream(stream_data)
        self.assertIsNotNone(evaluation_result)
        
        patch_triggered = self.connector.verify_and_trigger_response()
        self.assertIsInstance(patch_triggered, bool)


if __name__ == "__main__":
    unittest.main()