import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.telemetry_incident_trigger import (
    TelemetryIncidentTrigger,
    TelemetryTriggerException,
    telemetry_incident_trigger_function_or_class
)


class TestTelemetryIncidentTrigger(unittest.TestCase):

    def setUp(self):
        self.module_name = f"mod_{uuid.uuid4().hex[:8]}"
        self.trigger = TelemetryIncidentTrigger(module_name=self.module_name)

    def test_process_telemetry_normal(self):
        random_metric = random.randint(100, 999)
        random_sensor = f"sensor_{uuid.uuid4().hex[:6]}"
        telemetry_payload = {
            random_sensor: random_metric,
            "status": "active",
            "timestamp": random.randint(1000000, 9999999)
        }

        mock_eval_result = {
            "anomaly_detected": False,
            "incident_id": None
        }

        with patch.object(self.trigger.evaluator, 'evaluate', return_value=mock_eval_result) as mock_eval, \
             patch.object(self.trigger.aggregator, 'process_and_aggregate') as mock_agg:

            result = self.trigger.process_telemetry(telemetry_payload)

            mock_eval.assert_called_once_with(telemetry_payload)
            mock_agg.assert_not_called()
            self.assertTrue(result.get("success"))
            self.assertFalse(result.get("incident_triggered"))

    def test_process_telemetry_anomaly_detected(self):
        random_metric = random.randint(5000, 9999)
        random_sensor = f"sensor_{uuid.uuid4().hex[:6]}"
        incident_id = f"inc_{uuid.uuid4().hex[:8]}"
        reason_msg = f"Critical anomaly on {random_sensor}: {random_metric}"

        telemetry_payload = {
            random_sensor: random_metric,
            "status": "critical",
            "timestamp": random.randint(1000000, 9999999)
        }

        mock_eval_result = {
            "anomaly_detected": True,
            "incident_id": incident_id,
            "reason": reason_msg
        }

        with patch.object(self.trigger.evaluator, 'evaluate', return_value=mock_eval_result) as mock_eval, \
             patch.object(self.trigger.aggregator, 'process_and_aggregate') as mock_agg:

            result = self.trigger.process_telemetry(telemetry_payload)

            mock_eval.assert_called_once_with(telemetry_payload)
            mock_agg.assert_called_once()

            call_args = mock_agg.call_args[0]
            self.assertEqual(call_args[0], self.module_name)
            self.assertIsInstance(call_args[1], Exception)
            self.assertEqual(str(call_args[1]), reason_msg)
            self.assertEqual(call_args[3], incident_id)

            self.assertTrue(result.get("success"))
            self.assertTrue(result.get("incident_triggered"))
            self.assertEqual(result.get("incident_id"), incident_id)

    def test_process_telemetry_evaluator_exception(self):
        random_sensor = f"sensor_{uuid.uuid4().hex[:6]}"
        telemetry_payload = {
            random_sensor: random.randint(-999, -1)
        }
        error_msg = f"Evaluation failed for {uuid.uuid4().hex[:6]}"

        with patch.object(self.trigger.evaluator, 'evaluate', side_effect=Exception(error_msg)) as mock_eval:
            with self.assertRaises(TelemetryTriggerException) as ctx:
                self.trigger.process_telemetry(telemetry_payload)

            self.assertIn(error_msg, str(ctx.exception))
            mock_eval.assert_called_once_with(telemetry_payload)

    def test_evaluate_stream_success(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)
        expected_anomalies = random.randint(1, 5)
        mock_eval_stream_result = {
            "anomalies_found": expected_anomalies,
            "stream_processed": True
        }

        with patch.object(self.trigger.evaluator, 'evaluate_stream_source', return_value=mock_eval_stream_result) as mock_eval_stream:
            result = self.trigger.evaluate_stream(stream_data)

            mock_eval_stream.assert_called_once_with(stream_data)
            self.assertTrue(result.get("success"))
            self.assertEqual(result.get("anomalies_found"), expected_anomalies)
            self.assertTrue(result.get("stream_processed"))

    def test_evaluate_stream_exception(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        error_msg = f"Stream read error {uuid.uuid4().hex[:6]}"

        with patch.object(self.trigger.evaluator, 'evaluate_stream_source', side_effect=Exception(error_msg)) as mock_eval_stream:
            with self.assertRaises(TelemetryTriggerException) as ctx:
                self.trigger.evaluate_stream(stream_data)

            self.assertIn(error_msg, str(ctx.exception))
            mock_eval_stream.assert_called_once_with(stream_data)

    def test_functional_wrapper(self):
        random_metric = random.randint(10, 99)
        random_sensor = f"sensor_{uuid.uuid4().hex[:4]}"
        telemetry_payload = {
            random_sensor: random_metric
        }
        mock_eval_result = {
            "anomaly_detected": False,
            "incident_id": None
        }

        with patch('skills.telemetry_incident_trigger.TelemetryAnomalyEvaluatorCore.evaluate', return_value=mock_eval_result):
            result = telemetry_incident_trigger_function_or_class(telemetry_payload)
            self.assertTrue(result.get("success"))
            self.assertFalse(result.get("incident_triggered"))


if __name__ == '__main__':
    unittest.main()