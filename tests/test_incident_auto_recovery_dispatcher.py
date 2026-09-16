import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher


class TestIncidentAutoRecoveryDispatcher(unittest.TestCase):

    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()

    def test_dispatch_escalation_success(self):
        incident_id = uuid.uuid4().hex
        expected_result = {"status": "".join(random.choices(string.ascii_lowercase, k=8))}

        with patch.object(self.dispatcher.escalation_engine, 'process_escalation', return_value=expected_result) as mock_process:
            result = self.dispatcher.dispatch_escalation(incident_id)
            mock_process.assert_called_once_with(incident_id)
            self.assertEqual(result, expected_result)

    def test_handle_runtime_failure(self):
        module_name = uuid.uuid4().hex
        exc_message = uuid.uuid4().hex
        exception = RuntimeError(exc_message)
        context = {"ctx_key": uuid.uuid4().hex}
        expected_analysis = {"recovered": random.choice([True, False])}

        with patch.object(self.dispatcher.recovery_hub, 'analyze_and_recover', return_value=expected_analysis) as mock_analyze:
            result = self.dispatcher.handle_runtime_failure(module_name, exception, context)
            mock_analyze.assert_called_once_with(module_name, exception, context)
            self.assertEqual(result, expected_analysis)

    def test_run_full_recovery_cycle_success(self):
        module_name = uuid.uuid4().hex
        exception = ValueError(uuid.uuid4().hex)
        traceback_str = uuid.uuid4().hex
        incident_id = uuid.uuid4().hex
        patch_payload = {"patch": uuid.uuid4().hex}

        with patch.object(self.dispatcher.recovery_hub, 'capture_failure', return_value={"incident_id": incident_id}) as mock_capture, \
             patch.object(self.dispatcher.escalation_engine, 'check_and_trigger_patching', return_value=True) as mock_check, \
             patch.object(self.dispatcher.recovery_hub, 'generate_patch', return_value=patch_payload) as mock_generate, \
             patch.object(self.dispatcher.recovery_hub, 'deploy_and_verify', return_value=True) as mock_deploy:

            success = self.dispatcher.run_full_recovery_cycle(module_name, exception, traceback_str)

            mock_capture.assert_called_once_with(module_name, exception, traceback_str)
            mock_check.assert_called_once()
            mock_generate.assert_called_once_with(incident_id)
            mock_deploy.assert_called_once_with(incident_id, patch_payload)
            self.assertTrue(success)

    def test_run_full_recovery_cycle_no_patch_needed(self):
        module_name = uuid.uuid4().hex
        exception = TypeError(uuid.uuid4().hex)
        traceback_str = uuid.uuid4().hex
        incident_id = uuid.uuid4().hex

        with patch.object(self.dispatcher.recovery_hub, 'capture_failure', return_value=incident_id) as mock_capture, \
             patch.object(self.dispatcher.escalation_engine, 'check_and_trigger_patching', return_value=False) as mock_check, \
             patch.object(self.dispatcher.recovery_hub, 'generate_patch') as mock_generate, \
             patch.object(self.dispatcher.recovery_hub, 'deploy_and_verify') as mock_deploy:

            success = self.dispatcher.run_full_recovery_cycle(module_name, exception, traceback_str)

            mock_capture.assert_called_once_with(module_name, exception, traceback_str)
            mock_check.assert_called_once()
            mock_generate.assert_not_called()
            mock_deploy.assert_not_called()
            self.assertFalse(success)

    def test_evaluate_telemetry(self):
        telemetry_data = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch.object(self.dispatcher.escalation_engine, 'evaluate_system_telemetry_risks', return_value=telemetry_data) as mock_eval:
            result = self.dispatcher.evaluate_telemetry()
            mock_eval.assert_called_once()
            self.assertEqual(result, telemetry_data)

    def test_consume_and_process_stream(self):
        random_bytes = uuid.uuid4().hex.encode('utf-8')

        with patch.object(self.dispatcher.escalation_engine, 'consume_stream_data', return_value=random_bytes) as mock_consume:
            result = self.dispatcher.consume_and_process_stream()
            mock_consume.assert_called_once()
            self.assertEqual(result, random_bytes)

    def test_dispatch_recovery(self):
        incident_id = uuid.uuid4().hex
        module_name = uuid.uuid4().hex
        exception = Exception(uuid.uuid4().hex)
        expected_recovery_res = {"action": uuid.uuid4().hex}
        expected_escalation_res = {"level": random.randint(1, 5)}

        with patch.object(self.dispatcher.recovery_hub, 'analyze_and_recover', return_value=expected_recovery_res) as mock_recover, \
             patch.object(self.dispatcher.escalation_engine, 'process_escalation', return_value=expected_escalation_res) as mock_escalate:

            result = self.dispatcher.dispatch_recovery(incident_id, module_name, exception)

            mock_recover.assert_called_once_with(module_name, exception, {"incident_id": incident_id, "module_name": module_name})
            mock_escalate.assert_called_once_with(incident_id)

            self.assertEqual(result["incident_id"], incident_id)
            self.assertEqual(result["recovery_result"], expected_recovery_res)
            self.assertEqual(result["escalation_result"], expected_escalation_res)
            self.assertEqual(result["status"], "dispatched")


if __name__ == '__main__':
    unittest.main()