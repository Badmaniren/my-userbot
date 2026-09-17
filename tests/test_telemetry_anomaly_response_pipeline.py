import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.telemetry_anomaly_response_pipeline import (
    TelemetryAnomalyResponsePipeline,
    PipelineExecutionException
)

class TestTelemetryAnomalyResponsePipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = TelemetryAnomalyResponsePipeline()
        self.random_workspace = f"/var/workspace/{uuid.uuid4().hex}"
        self.random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL", "BLOCKER"])
        self.random_incident_id = str(uuid.uuid4())
        self.random_payload_key = "".join(random.choices(string.ascii_lowercase, k=8))
        self.random_payload_val = random.randint(1000, 99999)

    def test_pipeline_initialization(self):
        self.assertIsNotNone(self.pipeline)
        self.assertTrue(hasattr(self.pipeline, "evaluator_core"))
        self.assertTrue(hasattr(self.pipeline, "escalation_engine"))

    @patch('skills.telemetry_anomaly_response_pipeline.TelemetryAnomalyEvaluatorCore')
    @patch('skills.telemetry_anomaly_response_pipeline.IncidentAutoEscalationEngine')
    def test_process_telemetry_stream_success(self, mock_escalation_engine_cls, mock_evaluator_cls):
        mock_evaluator = mock_evaluator_cls.return_value
        mock_escalation = mock_escalation_engine_cls.return_value

        expected_eval_result = {
            uuid.uuid4().hex: random.choice([True, False]),
            "risk_score": random.uniform(0.1, 0.9)
        }
        mock_evaluator.evaluate_with_incident_trigger.return_value = expected_eval_result

        expected_escalation_result = {
            "incident_id": self.random_incident_id,
            "status": "ESCALATED",
            "code": random.randint(200, 500)
        }
        mock_escalation.process_escalation.return_value = expected_escalation_result

        pipeline = TelemetryAnomalyResponsePipeline()
        telemetry_stream_bytes = io.BytesIO(uuid.uuid4().bytes + random.randbytes(16))

        result = pipeline.process_telemetry_stream(telemetry_stream_bytes)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("evaluation"), expected_eval_result)
        self.assertEqual(result.get("escalation"), expected_escalation_result)
        mock_evaluator.evaluate_stream_source.assert_called_once()
        mock_escalation.evaluate_system_telemetry_risks.assert_called_once()

    @patch('skills.telemetry_anomaly_response_pipeline.TelemetryAnomalyEvaluatorCore')
    @patch('skills.telemetry_anomaly_response_pipeline.IncidentAutoEscalationEngine')
    def test_evaluate_and_respond_anomalies_detected(self, mock_escalation_engine_cls, mock_evaluator_cls):
        mock_evaluator = mock_evaluator_cls.return_value
        mock_escalation = mock_escalation_engine_cls.return_value

        mock_evaluator.evaluate.return_value = {
            "anomaly_detected": True,
            "severity": self.random_severity
        }

        mock_escalation.check_and_trigger_patching.return_value = True

        pipeline = TelemetryAnomalyResponsePipeline()
        test_payload = {
            self.random_payload_key: self.random_payload_val,
            "stream_uuid": uuid.uuid4().hex
        }

        response = pipeline.evaluate_and_respond(test_payload)

        self.assertIsInstance(response, dict)
        self.assertTrue(response.get("patch_triggered"))
        self.assertEqual(response.get("severity"), self.random_severity)
        mock_evaluator.evaluate.assert_called_once()
        mock_escalation.check_and_trigger_patching.assert_called_once()

    @patch('skills.telemetry_anomaly_response_pipeline.TelemetryAnomalyEvaluatorCore')
    @patch('skills.telemetry_anomaly_response_pipeline.IncidentAutoEscalationEngine')
    def test_pipeline_exception_handling(self, mock_escalation_engine_cls, mock_evaluator_cls):
        mock_evaluator = mock_evaluator_cls.return_value

        error_msg = f"Anomaly engine failure: {uuid.uuid4().hex}"
        mock_evaluator.evaluate.side_effect = Exception(error_msg)

        pipeline = TelemetryAnomalyResponsePipeline()
        bad_payload = {
            uuid.uuid4().hex: uuid.uuid4().hex
        }

        with self.assertRaises(PipelineExecutionException) as ctx:
            pipeline.evaluate_and_respond(bad_payload)

        self.assertIn(error_msg, str(ctx.exception))

    @patch('skills.telemetry_anomaly_response_pipeline.TelemetryAnomalyEvaluatorCore')
    @patch('skills.telemetry_anomaly_response_pipeline.IncidentAutoEscalationEngine')
    def test_consume_and_escalate_stream(self, mock_escalation_engine_cls, mock_evaluator_cls):
        mock_escalation = mock_escalation_engine_cls.return_value
        mock_evaluator = mock_evaluator_cls.return_value

        stream_garbage = random.randbytes(64)
        mock_escalation.consume_stream_data.return_value = stream_garbage

        sub_eval_result = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_evaluator.evaluate_stream_source.return_value = sub_eval_result

        pipeline = TelemetryAnomalyResponsePipeline()
        stream_report = pipeline.handle_stream_escalation_cycle()

        self.assertIsInstance(stream_report, dict)
        self.assertEqual(stream_report.get("consumed_bytes"), stream_garbage)
        self.assertEqual(stream_report.get("evaluation_metrics"), sub_eval_result)
        mock_escalation.consume_stream_data.assert_called_once()
        mock_evaluator.evaluate_stream_source.assert_called_once()

if __name__ == '__main__':
    unittest.main()