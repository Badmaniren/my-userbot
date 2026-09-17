import unittest
import uuid
import random
import io
from skills.telemetry_anomaly_response_pipeline import run_telemetry_anomaly_response_pipeline
from skills.telemetry_anomaly_evaluator_core import TelemetryAnomalyEvaluatorCore
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine

class IntegrationTestTelemetryAnomalyResponsePipeline(unittest.TestCase):

    def setUp(self):
        self.evaluator = TelemetryAnomalyEvaluatorCore()
        self.escalation_engine = IncidentAutoEscalationEngine()
        self.random_metric_id = str(uuid.uuid4())
        self.random_value = random.uniform(100.0, 999.9)

    def test_pipeline_integration_flow(self):
        payload = {
            "metric_id": self.random_metric_id,
            "anomaly_score": self.random_value,
            "stream_status": "critical"
        }

        result = run_telemetry_anomaly_response_pipeline(payload)

        self.assertIsInstance(result, dict)
        self.assertIn("evaluation_result", result)
        self.assertIn("escalation_result", result)

        valid_payload = {
            "stream_id": self.random_metric_id,
            "metric": self.random_metric_id,
            "value": self.random_value,
            "threshold": 50.0
        }
        eval_res = self.evaluator.evaluate(valid_payload)
        self.assertIsNotNone(eval_res)

        stream_data = self.escalation_engine.consume_stream_data()
        self.assertIsInstance(stream_data, bytes)

    def test_pipeline_stream_source_integration(self):
        stream_content = f"metric:{self.random_metric_id},value:{self.random_value}".encode('utf-8')
        stream_io = io.BytesIO(stream_content)

        eval_stream_res = self.evaluator.evaluate_stream_source(stream_io)
        self.assertIsNotNone(eval_stream_res)

        risk_assessment = self.escalation_engine.evaluate_system_telemetry_risks()
        self.assertIsInstance(risk_assessment, dict)

    def test_pipeline_incident_trigger_and_escalation(self):
        incident_id = f"inc-{uuid.uuid4()}"
        payload = {
            "stream_id": incident_id,
            "metric": "telemetry_spike",
            "value": float(random.randint(10, 100)),
            "threshold": 50.0
        }

        eval_trigger_res = self.evaluator.evaluate_with_incident_trigger(payload)
        self.assertIsNotNone(eval_trigger_res)

        escalation_res = self.escalation_engine.process_escalation(incident_id)
        self.assertIsInstance(escalation_res, dict)

        patch_triggered = self.escalation_engine.check_and_trigger_patching()
        self.assertIsInstance(patch_triggered, bool)

if __name__ == '__main__':
    unittest.main()