import unittest
from unittest.mock import patch
import io
import uuid
import random
from skills.telemetry_anomaly_bridge import (
    TelemetryAnomalyBridge,
    BridgeAnomalyException,
    BridgeProcessingException
)
from skills.telemetry_anomaly_evaluator_core import (
    AnomalyEvaluationException,
    InvalidTelemetryStreamException
)

class TestTelemetryAnomalyBridge(unittest.TestCase):
    def setUp(self):
        self.bridge = TelemetryAnomalyBridge()
        self.random_metric_id = uuid.uuid4().hex
        self.random_incident_id = uuid.uuid4().hex
        self.random_payload = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "metric_id": self.random_metric_id
        }
        self.random_bytes = bytes(uuid.uuid4().hex, 'utf-8')

    def test_normalize_payload_populates_missing_fields(self):
        raw_payload = {"metric_id": "test_m_1", "value": 150.0, "trigger_incident": True}
        normalized = self.bridge._normalize_payload(dict(raw_payload))
        self.assertEqual(normalized["stream_id"], "test_m_1")
        self.assertEqual(normalized["metric"], "test_m_1")
        self.assertEqual(normalized["value"], 150.0)
        self.assertEqual(normalized["threshold"], 149.0)

    def test_process_telemetry_payload_success(self):
        mock_eval_result = {"incident_id": self.random_incident_id, "status": "ANOMALY"}
        mock_escalation_result = {"status": "processed", "incident_id": self.random_incident_id}

        with patch.object(self.bridge.evaluator, 'evaluate_with_incident_trigger', return_value=mock_eval_result) as mock_eval, \
             patch.object(self.bridge.escalation_engine, 'process_escalation', return_value=mock_escalation_result) as mock_esc:

            result = self.bridge.process_telemetry_payload(self.random_payload)

            mock_eval.assert_called_once_with(self.random_payload)
            mock_esc.assert_called_once_with(self.random_incident_id)
            self.assertEqual(result["evaluation"], mock_eval_result)
            self.assertEqual(result["escalation"], mock_escalation_result)
            self.assertEqual(result["status"], "PROCESSED")

    def test_process_telemetry_payload_no_incident(self):
        mock_eval_result = {"incident_id": None, "status": "NORMAL"}

        with patch.object(self.bridge.evaluator, 'evaluate_with_incident_trigger', return_value=mock_eval_result) as mock_eval, \
             patch.object(self.bridge.escalation_engine, 'process_escalation') as mock_esc:

            result = self.bridge.process_telemetry_payload(self.random_payload)

            mock_eval.assert_called_once_with(self.random_payload)
            mock_esc.assert_not_called()
            self.assertEqual(result["evaluation"], mock_eval_result)
            self.assertIsNone(result["escalation"])
            self.assertEqual(result["status"], "SKIPPED_NO_INCIDENT")

    def test_process_telemetry_payload_anomaly_exception(self):
        err_msg = uuid.uuid4().hex
        with patch.object(self.bridge.evaluator, 'evaluate_with_incident_trigger', side_effect=AnomalyEvaluationException(err_msg)):
            with self.assertRaises(BridgeAnomalyException) as ctx:
                self.bridge.process_telemetry_payload(self.random_payload)
            self.assertIn(err_msg, str(ctx.exception))

    def test_process_telemetry_payload_processing_exception(self):
        err_msg = uuid.uuid4().hex
        with patch.object(self.bridge.evaluator, 'evaluate_with_incident_trigger', side_effect=InvalidTelemetryStreamException(err_msg)):
            with self.assertRaises(BridgeProcessingException) as ctx:
                self.bridge.process_telemetry_payload(self.random_payload)
            self.assertIn(err_msg, str(ctx.exception))

    def test_process_stream(self):
        stream_io = io.BytesIO(self.random_bytes)
        mock_stream_eval = {"incident_id": self.random_incident_id}
        mock_escalation = {"status": "processed", "id": self.random_incident_id}

        with patch.object(self.bridge.evaluator, 'evaluate_stream_source', return_value=mock_stream_eval) as mock_eval, \
             patch.object(self.bridge.escalation_engine, 'process_escalation', return_value=mock_escalation) as mock_esc:

            result = self.bridge.process_stream(stream_io)

            mock_eval.assert_called_once_with(stream_io)
            mock_esc.assert_called_once_with(self.random_incident_id)
            self.assertEqual(result["stream_evaluation"], mock_stream_eval)
            self.assertEqual(result["escalation_response"], mock_escalation)

    def test_evaluate_and_patch_risks(self):
        mock_risk = {uuid.uuid4().hex: random.randint(1, 100)}
        mock_patch = random.choice([True, False])

        with patch.object(self.bridge.escalation_engine, 'evaluate_system_telemetry_risks', return_value=mock_risk) as mock_eval_risk, \
             patch.object(self.bridge.escalation_engine, 'check_and_trigger_patching', return_value=mock_patch) as mock_chk_patch:

            result = self.bridge.evaluate_and_patch_risks()

            mock_eval_risk.assert_called_once()
            mock_chk_patch.assert_called_once()
            self.assertEqual(result["risk_report"], mock_risk)
            self.assertEqual(result["patch_triggered"], mock_patch)

    def test_process_and_escalate_success(self):
        mock_eval = {"incident_id": self.random_incident_id}
        mock_esc = {"status": "processed", "incident_id": self.random_incident_id}

        with patch.object(self.bridge.evaluator, 'evaluate_with_incident_trigger', return_value=mock_eval), \
             patch.object(self.bridge.escalation_engine, 'process_escalation', return_value=mock_esc) as mock_escalation_call:

            result = self.bridge.process_and_escalate(self.random_payload)

            mock_escalation_call.assert_called_once_with(self.random_incident_id)
            self.assertEqual(result["escalation_status"], "escalated")
            self.assertEqual(result["incident_id"], self.random_incident_id)
            self.assertEqual(result["evaluation"], mock_eval)

    def test_process_and_escalate_exception_fallback(self):
        with patch.object(self.bridge.evaluator, 'evaluate_with_incident_trigger', side_effect=Exception(uuid.uuid4().hex)), \
             patch.object(self.bridge.escalation_engine, 'process_escalation', return_value={}) as mock_escalation_call:

            result = self.bridge.process_and_escalate(self.random_payload)

            mock_escalation_call.assert_called_once()
            self.assertEqual(result["escalation_status"], "escalated")
            self.assertEqual(result["incident_id"], self.random_payload.get("metric_id"))
            self.assertEqual(result["evaluation"]["status"], "ANOMALY_DETECTED")

    def test_handle_stream_payload_success(self):
        mock_stream_eval = {"incident_id": self.random_incident_id, "status": "evaluated"}
        mock_escalation = {"status": "processed"}

        with patch.object(self.bridge.evaluator, 'evaluate_stream_source', return_value=mock_stream_eval), \
             patch.object(self.bridge.escalation_engine, 'process_escalation', return_value=mock_escalation) as mock_esc:

            result = self.bridge.handle_stream_payload(self.random_bytes)

            mock_esc.assert_called_once_with(self.random_incident_id)
            self.assertTrue(result["escalated"])
            self.assertEqual(result["status"], "handled")
            self.assertEqual(result["incident_id"], self.random_incident_id)
            self.assertEqual(result["escalation"], mock_escalation)
            self.assertEqual(result["stream_evaluation"], mock_stream_eval)

    def test_handle_stream_payload_exception_fallback(self):
        with patch.object(self.bridge.evaluator, 'evaluate_stream_source', side_effect=Exception(uuid.uuid4().hex)), \
             patch.object(self.bridge.escalation_engine, 'process_escalation', return_value={"status": "processed"}) as mock_esc:

            result = self.bridge.handle_stream_payload(self.random_bytes)

            mock_esc.assert_called_once_with("stream_incident_id")
            self.assertTrue(result["escalated"])
            self.assertEqual(result["incident_id"], "stream_incident_id")
            self.assertEqual(result["stream_evaluation"]["status"], "evaluated")