import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher


class TestIncidentAutoRecoveryDispatcher(unittest.TestCase):

    def setUp(self):
        self.random_incident_id = str(uuid.uuid4())
        self.random_module_name = "".join(random.choices(string.ascii_lowercase, k=10))
        self.random_traceback = "".join(random.choices(string.printable, k=50))
        self.random_context = {
            "".join(random.choices(string.ascii_lowercase, k=5)): random.randint(1, 100)
            for _ in range(3)
        }
        self.random_exception = RuntimeError("".join(random.choices(string.ascii_letters, k=15)))

    @patch("skills.incident_auto_recovery_dispatcher.IncidentAutoEscalationEngine")
    @patch("skills.incident_auto_recovery_dispatcher.ErrorRecoveryHub")
    def test_init_components(self, mock_recovery_hub, mock_escalation_engine):
        dispatcher = IncidentAutoRecoveryDispatcher()
        mock_escalation_engine.assert_called_once()
        mock_recovery_hub.assert_called_once()
        self.assertIsInstance(dispatcher, IncidentAutoRecoveryDispatcher)

    @patch("skills.incident_auto_recovery_dispatcher.IncidentAutoEscalationEngine")
    @patch("skills.incident_auto_recovery_dispatcher.ErrorRecoveryHub")
    def test_dispatch_escalation(self, mock_recovery_hub, mock_escalation_engine):
        expected_result = {"status": "".join(random.choices(string.ascii_lowercase, k=8))}
        instance_engine = mock_escalation_engine.return_value
        instance_engine.process_escalation.return_value = expected_result

        dispatcher = IncidentAutoRecoveryDispatcher()
        result = dispatcher.dispatch_escalation(self.random_incident_id)

        instance_engine.process_escalation.assert_called_once_with(self.random_incident_id)
        self.assertEqual(result, expected_result)

    @patch("skills.incident_auto_recovery_dispatcher.IncidentAutoEscalationEngine")
    @patch("skills.incident_auto_recovery_dispatcher.ErrorRecoveryHub")
    def test_handle_runtime_failure(self, mock_recovery_hub, mock_escalation_engine):
        expected_result = {"recovered": random.choice([True, False])}
        instance_hub = mock_recovery_hub.return_value
        instance_hub.analyze_and_recover.return_value = expected_result

        dispatcher = IncidentAutoRecoveryDispatcher()
        result = dispatcher.handle_runtime_failure(
            self.random_module_name, self.random_exception, self.random_context
        )

        instance_hub.analyze_and_recover.assert_called_once_with(
            self.random_module_name, self.random_exception, self.random_context
        )
        self.assertEqual(result, expected_result)

    @patch("skills.incident_auto_recovery_dispatcher.IncidentAutoEscalationEngine")
    @patch("skills.incident_auto_recovery_dispatcher.ErrorRecoveryHub")
    def test_run_full_recovery_cycle_success(self, mock_recovery_hub, mock_escalation_engine):
        instance_hub = mock_recovery_hub.return_value
        instance_engine = mock_escalation_engine.return_value

        instance_hub.capture_failure.return_value = self.random_incident_id
        instance_engine.check_and_trigger_patching.return_value = True
        
        patch_payload = {"patch_id": str(uuid.uuid4())}
        instance_hub.generate_patch.return_value = patch_payload
        instance_hub.deploy_and_verify.return_value = True

        dispatcher = IncidentAutoRecoveryDispatcher()
        result = dispatcher.run_full_recovery_cycle(
            self.random_module_name, self.random_exception, self.random_traceback
        )

        instance_hub.capture_failure.assert_called_once_with(
            self.random_module_name, self.random_exception, self.random_traceback
        )
        instance_engine.check_and_trigger_patching.assert_called_once()
        instance_hub.generate_patch.assert_called_once_with(self.random_incident_id)
        instance_hub.deploy_and_verify.assert_called_once_with(self.random_incident_id, patch_payload)
        self.assertTrue(result)

    @patch("skills.incident_auto_recovery_dispatcher.IncidentAutoEscalationEngine")
    @patch("skills.incident_auto_recovery_dispatcher.ErrorRecoveryHub")
    def test_run_full_recovery_cycle_dict_incident_id(self, mock_recovery_hub, mock_escalation_engine):
        instance_hub = mock_recovery_hub.return_value
        instance_engine = mock_escalation_engine.return_value

        dict_incident = {"incident_id": self.random_incident_id}
        instance_hub.capture_failure.return_value = dict_incident
        instance_engine.check_and_trigger_patching.return_value = True
        
        patch_payload = {"data": random.randint(100, 999)}
        instance_hub.generate_patch.return_value = patch_payload
        instance_hub.deploy_and_verify.return_value = False

        dispatcher = IncidentAutoRecoveryDispatcher()
        result = dispatcher.run_full_recovery_cycle(
            self.random_module_name, self.random_exception, self.random_traceback
        )

        instance_hub.generate_patch.assert_called_once_with(self.random_incident_id)
        self.assertFalse(result)

    @patch("skills.incident_auto_recovery_dispatcher.IncidentAutoEscalationEngine")
    @patch("skills.incident_auto_recovery_dispatcher.ErrorRecoveryHub")
    def test_run_full_recovery_cycle_no_patch(self, mock_recovery_hub, mock_escalation_engine):
        instance_hub = mock_recovery_hub.return_value
        instance_engine = mock_escalation_engine.return_value

        instance_hub.capture_failure.return_value = self.random_incident_id
        instance_engine.check_and_trigger_patching.return_value = False

        dispatcher = IncidentAutoRecoveryDispatcher()
        result = dispatcher.run_full_recovery_cycle(
            self.random_module_name, self.random_exception, self.random_traceback
        )

        instance_engine.check_and_trigger_patching.assert_called_once()
        instance_hub.generate_patch.assert_not_called()
        self.assertFalse(result)

    @patch("skills.incident_auto_recovery_dispatcher.IncidentAutoEscalationEngine")
    @patch("skills.incident_auto_recovery_dispatcher.ErrorRecoveryHub")
    def test_evaluate_telemetry(self, mock_recovery_hub, mock_escalation_engine):
        telemetry_data = {"risk_level": "".join(random.choices(string.ascii_uppercase, k=5))}
        instance_engine = mock_escalation_engine.return_value
        instance_engine.evaluate_system_telemetry_risks.return_value = telemetry_data

        dispatcher = IncidentAutoRecoveryDispatcher()
        result = dispatcher.evaluate_telemetry()

        instance_engine.evaluate_system_telemetry_risks.assert_called_once()
        self.assertEqual(result, telemetry_data)

    @patch("skills.incident_auto_recovery_dispatcher.IncidentAutoEscalationEngine")
    @patch("skills.incident_auto_recovery_dispatcher.ErrorRecoveryHub")
    def test_consume_and_process_stream(self, mock_recovery_hub, mock_escalation_engine):
        stream_bytes = io.BytesIO(b"".join(random.choices(string.printable.encode(), k=32))).read()
        instance_engine = mock_escalation_engine.return_value
        instance_engine.consume_stream_data.return_value = stream_bytes

        dispatcher = IncidentAutoRecoveryDispatcher()
        result = dispatcher.consume_and_process_stream()

        instance_engine.consume_stream_data.assert_called_once()
        self.assertEqual(result, stream_bytes)

    @patch("skills.incident_auto_recovery_dispatcher.IncidentAutoEscalationEngine")
    @patch("skills.incident_auto_recovery_dispatcher.ErrorRecoveryHub")
    def test_dispatch_recovery(self, mock_recovery_hub, mock_escalation_engine):
        instance_hub = mock_recovery_hub.return_value
        instance_engine = mock_escalation_engine.return_value

        mock_recovery_result = {"status": "".join(random.choices(string.ascii_lowercase, k=6))}
        mock_escalation_result = {"escalated": random.choice([True, False])}

        instance_hub.analyze_and_recover.return_value = mock_recovery_result
        instance_engine.process_escalation.return_value = mock_escalation_result

        dispatcher = IncidentAutoRecoveryDispatcher()
        result = dispatcher.dispatch_recovery(
            self.random_incident_id, self.random_module_name, self.random_exception
        )

        expected_context = {
            "incident_id": self.random_incident_id,
            "module_name": self.random_module_name
        }

        instance_hub.analyze_and_recover.assert_called_once_with(
            self.random_module_name, self.random_exception, expected_context
        )
        instance_engine.process_escalation.assert_called_once_with(self.random_incident_id)

        self.assertEqual(result["incident_id"], self.random_incident_id)
        self.assertEqual(result["recovery_result"], mock_recovery_result)
        self.assertEqual(result["escalation_result"], mock_escalation_result)
        self.assertEqual(result["status"], "dispatched")


if __name__ == "__main__":
    unittest.main()