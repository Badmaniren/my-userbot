import unittest
from unittest.mock import MagicMock, patch
import io
import uuid
import random
import string

from skills.telemetry_anomaly_response_connector import (
    TelemetryAnomalyResponseConnector,
    ConnectorException,
    connect_telemetry_to_escalation
)
from skills.telemetry_anomaly_evaluator_core import (
    AnomalyEvaluationException,
    InvalidTelemetryStreamException
)


class TestTelemetryAnomalyResponseConnector(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = f"/tmp/{uuid.uuid4().hex}"
        self.mock_evaluator = MagicMock()
        self.mock_escalation_engine = MagicMock()
        self.connector = TelemetryAnomalyResponseConnector(
            workspace_dir=self.workspace_dir,
            evaluator=self.mock_evaluator,
            escalation_engine=self.mock_escalation_engine
        )

    def test_handle_telemetry_and_respond_success_anomaly(self):
        rand_incident_id = uuid.uuid4().hex
        rand_status = random.choice(["CRITICAL", "HIGH", "EMERGENCY"])
        telemetry_payload = {
            "id": uuid.uuid4().hex,
            "incident_id": rand_incident_id,
            "status": rand_status
        }
        
        evaluation_mock = {
            "is_anomaly": True,
            "incident_id": rand_incident_id,
            "severity": rand_status
        }
        self.mock_evaluator.evaluate_with_incident_trigger.return_value = evaluation_mock
        
        rand_escalation_response = {"escalated": True, "ticket": uuid.uuid4().hex}
        self.mock_escalation_engine.process_escalation.return_value = rand_escalation_response

        result = self.connector.handle_telemetry_and_respond(telemetry_payload)

        self.assertTrue(result["anomaly_handled"])
        self.assertEqual(result["evaluation"], evaluation_mock)
        self.assertEqual(result["escalation"], rand_escalation_response)
        self.mock_evaluator.evaluate_with_incident_trigger.assert_called_once_with(telemetry_payload)
        self.mock_escalation_engine.process_escalation.assert_called_once_with(rand_incident_id)

    def test_handle_telemetry_and_respond_no_anomaly(self):
        telemetry_payload = {
            "id": uuid.uuid4().hex,
            "incident_id": uuid.uuid4().hex,
            "status": "NORMAL"
        }
        
        evaluation_mock = {
            "is_anomaly": False,
            "incident_id": telemetry_payload["incident_id"],
            "severity": "LOW"
        }
        self.mock_evaluator.evaluate_with_incident_trigger.return_value = evaluation_mock

        result = self.connector.handle_telemetry_and_respond(telemetry_payload)

        self.assertFalse(result["anomaly_handled"])
        self.assertEqual(result["evaluation"], evaluation_mock)
        self.assertIsNone(result["escalation"])
        self.mock_escalation_engine.process_escalation.assert_not_called()

    def test_handle_telemetry_and_respond_fallback_on_invalid_stream(self):
        rand_incident_id = uuid.uuid4().hex
        rand_status = random.choice(["CRITICAL", "FATAL"])
        telemetry_payload = {
            "incident_id": rand_incident_id,
            "status": rand_status,
            "garbage": uuid.uuid4().hex
        }
        
        self.mock_evaluator.evaluate_with_incident_trigger.side_effect = InvalidTelemetryStreamException(uuid.uuid4().hex)
        rand_escalation_response = {"status": "forced_escalation_active", "code": random.randint(100, 999)}
        self.mock_escalation_engine.process_escalation.return_value = rand_escalation_response

        result = self.connector.handle_telemetry_and_respond(telemetry_payload)

        self.assertTrue(result["anomaly_handled"])
        self.assertEqual(result["evaluation"]["incident_id"], rand_incident_id)
        self.assertEqual(result["evaluation"]["severity"], rand_status)
        self.assertEqual(result["escalation"], rand_escalation_response)
        self.mock_escalation_engine.process_escalation.assert_called_once_with(rand_incident_id)

    def test_handle_telemetry_and_respond_anomaly_exception_raises_connector_exception(self):
        telemetry_payload = {"id": uuid.uuid4().hex}
        err_msg = uuid.uuid4().hex
        self.mock_evaluator.evaluate_with_incident_trigger.side_effect = AnomalyEvaluationException(err_msg)

        with self.assertRaises(ConnectorException) as ctx:
            self.connector.handle_telemetry_and_respond(telemetry_payload)
        
        self.assertIn(err_msg, str(ctx.exception))

    def test_handle_telemetry_and_respond_generic_exception_raises_connector_exception(self):
        telemetry_payload = {"id": uuid.uuid4().hex}
        err_msg = uuid.uuid4().hex
        self.mock_evaluator.evaluate_with_incident_trigger.side_effect = RuntimeError(err_msg)

        with self.assertRaises(ConnectorException) as ctx:
            self.connector.handle_telemetry_and_respond(telemetry_payload)
        
        self.assertIn(err_msg, str(ctx.exception))

    def test_process_telemetry_stream_success(self):
        rand_bytes = ''.join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')
        stream_io = io.BytesIO(rand_bytes)
        
        rand_incident_id = uuid.uuid4().hex
        stream_result_mock = {"incident_id": rand_incident_id, "metrics": random.randint(1, 100)}
        self.mock_evaluator.evaluate_stream_source.return_value = stream_result_mock
        
        escalation_result_mock = {"escalated_stream": True, "token": uuid.uuid4().hex}
        self.mock_escalation_engine.process_escalation.return_value = escalation_result_mock

        result = self.connector.process_telemetry_stream(stream_io)

        self.assertEqual(result["stream_result"], stream_result_mock)
        self.assertEqual(result["escalation_result"], escalation_result_mock)
        self.mock_evaluator.evaluate_stream_source.assert_called_once_with(stream_io)
        self.mock_escalation_engine.process_escalation.assert_called_once_with(rand_incident_id)

    def test_process_telemetry_stream_invalid_stream_exception(self):
        stream_io = io.BytesIO(b"")
        err_msg = uuid.uuid4().hex
        self.mock_evaluator.evaluate_stream_source.side_effect = InvalidTelemetryStreamException(err_msg)

        with self.assertRaises(ConnectorException) as ctx:
            self.connector.process_telemetry_stream(stream_io)
        
        self.assertIn(err_msg, str(ctx.exception))

    def test_evaluate_and_mitigate_risks(self):
        risk_assessment_mock = {"risk_level": uuid.uuid4().hex, "score": random.random()}
        patch_triggered_mock = random.choice([True, False])
        
        self.mock_escalation_engine.evaluate_system_telemetry_risks.return_value = risk_assessment_mock
        self.mock_escalation_engine.check_and_trigger_patching.return_value = patch_triggered_mock

        result = self.connector.evaluate_and_mitigate_risks()

        self.assertEqual(result["risk_assessment"], risk_assessment_mock)
        self.assertEqual(result["patch_triggered"], patch_triggered_mock)
        self.mock_escalation_engine.evaluate_system_telemetry_risks.assert_called_once()
        self.mock_escalation_engine.check_and_trigger_patching.assert_called_once()

    def test_process_incoming_stream(self):
        rand_stream_data = ''.join(random.choices(string.printable, k=128)).encode('utf-8')
        eval_result_mock = {"status": uuid.uuid4().hex, "processed": True}
        self.mock_evaluator.evaluate_stream_source.return_value = eval_result_mock

        result = self.connector.process_incoming_stream(rand_stream_data)

        self.assertEqual(result, eval_result_mock)
        self.mock_evaluator.evaluate_stream_source.assert_called_once()
        called_args = self.mock_evaluator.evaluate_stream_source.call_args[0][0]
        self.assertIsInstance(called_args, io.BytesIO)
        self.assertEqual(called_args.read(), rand_stream_data)

    def test_verify_and_trigger_response(self):
        expected_bool = random.choice([True, False])
        self.mock_escalation_engine.check_and_trigger_patching.return_value = expected_bool

        result = self.connector.verify_and_trigger_response()

        self.assertEqual(result, expected_bool)
        self.mock_escalation_engine.check_and_trigger_patching.assert_called_once()

    def test_global_connect_telemetry_to_escalation_function(self):
        rand_payload = {"incident_id": uuid.uuid4().hex, "status": "CRITICAL"}
        rand_eval = {"is_anomaly": True, "incident_id": rand_payload["incident_id"], "severity": "CRITICAL"}
        rand_esc = {"processed": True}

        with patch("skills.telemetry_anomaly_response_connector.TelemetryAnomalyResponseConnector") as MockConnectorClass:
            instance_mock = MockConnectorClass.return_value
            instance_mock.handle_telemetry_and_respond.return_value = {
                "anomaly_handled": True,
                "evaluation": rand_eval,
                "escalation": rand_esc
            }

            res = connect_telemetry_to_escalation(rand_payload)

            MockConnectorClass.assert_called_once_with()
            instance_mock.handle_telemetry_and_respond.assert_called_once_with(rand_payload)
            self.assertTrue(res["anomaly_handled"])
            self.assertEqual(res["evaluation"], rand_eval)
            self.assertEqual(res["escalation"], rand_esc)