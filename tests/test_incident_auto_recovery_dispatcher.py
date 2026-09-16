import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import string

from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher


class TestIncidentAutoRecoveryDispatcher(unittest.TestCase):

    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()

    def test_dispatch_escalation(self):
        random_incident_id = uuid.uuid4().hex
        expected_result = {"status": uuid.uuid4().hex, "code": random.randint(100, 500)}

        with patch.object(self.dispatcher.escalation_engine, 'process_escalation', return_value=expected_result) as mock_process:
            result = self.dispatcher.dispatch_escalation(random_incident_id)
            mock_process.assert_called_once_with(random_incident_id)
            self.assertEqual(result, expected_result)

    def test_handle_runtime_failure(self):
        random_module = "".join(random.choices(string.ascii_lowercase, k=10))
        random_error_msg = uuid.uuid4().hex
        random_exception = RuntimeError(random_error_msg)
        random_context = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_recovery = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch.object(self.dispatcher.recovery_hub, 'analyze_and_recover', return_value=expected_recovery) as mock_analyze:
            result = self.dispatcher.handle_runtime_failure(random_module, random_exception, random_context)
            mock_analyze.assert_called_once_with(random_module, random_exception, random_context)
            self.assertEqual(result, expected_recovery)

    def test_run_full_recovery_cycle_success(self):
        random_module = "".join(random.choices(string.ascii_lowercase, k=8))
        random_exception = ValueError(uuid.uuid4().hex)
        random_traceback = uuid.uuid4().hex
        random_incident_id = uuid.uuid4().hex
        random_patch = uuid.uuid4().hex

        with patch.object(self.dispatcher.recovery_hub, 'capture_failure', return_value=random_incident_id) as mock_capture, \
             patch.object(self.dispatcher.escalation_engine, 'check_and_trigger_patching', return_value=True) as mock_check, \
             patch.object(self.dispatcher.recovery_hub, 'generate_patch', return_value=random_patch) as mock_generate, \
             patch.object(self.dispatcher.recovery_hub, 'deploy_and_verify', return_value=True) as mock_deploy:

            success = self.dispatcher.run_full_recovery_cycle(random_module, random_exception, random_traceback)

            mock_capture.assert_called_once_with(random_module, random_exception, random_traceback)
            mock_check.assert_called_once()
            mock_generate.assert_called_once_with(random_incident_id)
            mock_deploy.assert_called_once_with(random_incident_id, random_patch)
            self.assertTrue(success)

    def test_run_full_recovery_cycle_dict_incident_id(self):
        random_module = "".join(random.choices(string.ascii_lowercase, k=6))
        random_exception = TypeError(uuid.uuid4().hex)
        random_traceback = uuid.uuid4().hex
        random_incident_id = uuid.uuid4().hex
        incident_dict = {"incident_id": random_incident_id}
        random_patch = uuid.uuid4().hex

        with patch.object(self.dispatcher.recovery_hub, 'capture_failure', return_value=incident_dict) as mock_capture, \
             patch.object(self.dispatcher.escalation_engine, 'check_and_trigger_patching', return_value=True) as mock_check, \
             patch.object(self.dispatcher.recovery_hub, 'generate_patch', return_value=random_patch) as mock_generate, \
             patch.object(self.dispatcher.recovery_hub, 'deploy_and_verify', return_value=1) as mock_deploy:

            success = self.dispatcher.run_full_recovery_cycle(random_module, random_exception, random_traceback)

            mock_capture.assert_called_once_with(random_module, random_exception, random_traceback)
            mock_generate.assert_called_once_with(random_incident_id)
            mock_deploy.assert_called_once_with(random_incident_id, random_patch)
            self.assertTrue(success)

    def test_run_full_recovery_cycle_no_patch(self):
        random_module = "".join(random.choices(string.ascii_lowercase, k=7))
        random_exception = KeyError(uuid.uuid4().hex)
        random_traceback = uuid.uuid4().hex
        random_incident_id = uuid.uuid4().hex

        with patch.object(self.dispatcher.recovery_hub, 'capture_failure', return_value=random_incident_id) as mock_capture, \
             patch.object(self.dispatcher.escalation_engine, 'check_and_trigger_patching', return_value=False) as mock_check, \
             patch.object(self.dispatcher.recovery_hub, 'generate_patch') as mock_generate:

            success = self.dispatcher.run_full_recovery_cycle(random_module, random_exception, random_traceback)

            mock_capture.assert_called_once_with(random_module, random_exception, random_traceback)
            mock_check.assert_called_once()
            mock_generate.assert_not_called()
            self.assertFalse(success)

    def test_evaluate_telemetry(self):
        expected_telemetry = {uuid.uuid4().hex: random.randint(10, 100)}

        with patch.object(self.dispatcher.escalation_engine, 'evaluate_system_telemetry_risks', return_value=expected_telemetry) as mock_eval:
            result = self.dispatcher.evaluate_telemetry()
            mock_eval.assert_called_once()
            self.assertEqual(result, expected_telemetry)

    def test_consume_and_process_stream(self):
        random_bytes = uuid.uuid4().hex.encode('utf-8')
        stream_mock = io.BytesIO(random_bytes)

        with patch.object(self.dispatcher.escalation_engine, 'consume_stream_data', return_value=stream_mock.read()) as mock_consume:
            result = self.dispatcher.consume_and_process_stream()
            mock_consume.assert_called_once()
            self.assertEqual(result, random_bytes)

    def test_dispatch_recovery(self):
        random_incident_id = uuid.uuid4().hex
        random_module = "".join(random.choices(string.ascii_lowercase, k=9))
        random_exception = Exception(uuid.uuid4().hex)
        expected_recovery_res = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_escalation_res = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.dispatcher.recovery_hub, 'analyze_and_recover', return_value=expected_recovery_res) as mock_recover, \
             patch.object(self.dispatcher.escalation_engine, 'process_escalation', return_value=expected_escalation_res) as mock_escalate:

            result = self.dispatcher.dispatch_recovery(random_incident_id, random_module, random_exception)

            expected_context = {"incident_id": random_incident_id, "module_name": random_module}
            mock_recover.assert_called_once_with(random_module, random_exception, expected_context)
            mock_escalate.assert_called_once_with(random_incident_id)

            self.assertEqual(result, {
                "incident_id": random_incident_id,
                "recovery_result": expected_recovery_res,
                "escalation_result": expected_escalation_res,
                "status": "dispatched"
            })


if __name__ == '__main__':
    unittest.main()