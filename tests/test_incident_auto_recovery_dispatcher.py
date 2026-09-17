import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher


class TestIncidentAutoRecoveryDispatcher(unittest.TestCase):

    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()
        self.rand_incident_id = uuid.uuid4().hex
        self.rand_module_name = f"module_{uuid.uuid4().hex[:6]}"
        self.rand_error_msg = f"error_{uuid.uuid4().hex[:6]}"
        self.rand_traceback = f"Traceback (most recent call last):\n  File \"<string>\", line 1, in <module>\nException: {self.rand_error_msg}"

    def test_dispatch_escalation_success(self):
        with patch.object(self.dispatcher.escalation_engine, 'process_escalation') as mock_process:
            expected_result = {"status": "escalated", "id": self.rand_incident_id}
            mock_process.return_value = expected_result

            result = self.dispatcher.dispatch_escalation(self.rand_incident_id)

            mock_process.assert_called_once_with(self.rand_incident_id)
            self.assertEqual(result, expected_result)

    def test_handle_runtime_failure_success(self):
        with patch.object(self.dispatcher.recovery_hub, 'analyze_and_recover') as mock_analyze:
            rand_context = {"uuid": uuid.uuid4().hex, "retry_count": random.randint(1, 5)}
            exc = RuntimeError(self.rand_error_msg)
            expected_output = {"recovered": True, "details": uuid.uuid4().hex}
            mock_analyze.return_value = expected_output

            result = self.dispatcher.handle_runtime_failure(self.rand_module_name, exc, rand_context)

            mock_analyze.assert_called_once_with(self.rand_module_name, exc, rand_context)
            self.assertEqual(result, expected_output)

    def test_run_full_recovery_cycle_with_patching(self):
        with patch.object(self.dispatcher.recovery_hub, 'capture_failure') as mock_capture, \
             patch.object(self.dispatcher.escalation_engine, 'check_and_trigger_patching') as mock_check_patch, \
             patch.object(self.dispatcher.recovery_hub, 'generate_patch') as mock_gen_patch, \
             patch.object(self.dispatcher.recovery_hub, 'deploy_and_verify') as mock_deploy:

            mock_capture.return_value = {"incident_id": self.rand_incident_id}
            mock_check_patch.return_value = True
            rand_patch_payload = {"patch_data": uuid.uuid4().hex}
            mock_gen_patch.return_value = rand_patch_payload
            mock_deploy.return_value = True

            exc = Exception(self.rand_error_msg)
            success = self.dispatcher.run_full_recovery_cycle(self.rand_module_name, exc, self.rand_traceback)

            self.assertTrue(success)
            mock_capture.assert_called_once_with(self.rand_module_name, exc, self.rand_traceback)
            mock_check_patch.assert_called_once()
            mock_gen_patch.assert_called_once_with(self.rand_incident_id)
            mock_deploy.assert_called_once_with(self.rand_incident_id, rand_patch_payload)

    def test_run_full_recovery_cycle_no_patching(self):
        with patch.object(self.dispatcher.recovery_hub, 'capture_failure') as mock_capture, \
             patch.object(self.dispatcher.escalation_engine, 'check_and_trigger_patching') as mock_check_patch, \
             patch.object(self.dispatcher.recovery_hub, 'generate_patch') as mock_gen_patch, \
             patch.object(self.dispatcher.recovery_hub, 'deploy_and_verify') as mock_deploy:

            mock_capture.return_value = self.rand_incident_id
            mock_check_patch.return_value = False

            exc = Exception(self.rand_error_msg)
            success = self.dispatcher.run_full_recovery_cycle(self.rand_module_name, exc, self.rand_traceback)

            self.assertFalse(success)
            mock_capture.assert_called_once_with(self.rand_module_name, exc, self.rand_traceback)
            mock_check_patch.assert_called_once()
            mock_gen_patch.assert_not_called()
            mock_deploy.assert_not_called()

    def test_evaluate_telemetry(self):
        with patch.object(self.dispatcher.escalation_engine, 'evaluate_system_telemetry_risks') as mock_eval:
            rand_telemetry = {"risk_level": uuid.uuid4().hex, "score": random.random()}
            mock_eval.return_value = rand_telemetry

            result = self.dispatcher.evaluate_telemetry()

            mock_eval.assert_called_once()
            self.assertEqual(result, rand_telemetry)

    def test_consume_and_process_stream(self):
        with patch.object(self.dispatcher.escalation_engine, 'consume_stream_data') as mock_consume:
            rand_bytes = uuid.uuid4().hex.encode('utf-8')
            mock_consume.return_value = rand_bytes

            result = self.dispatcher.consume_and_process_stream()

            mock_consume.assert_called_once()
            self.assertEqual(result, rand_bytes)

    def test_dispatch_recovery(self):
        with patch.object(self.dispatcher.recovery_hub, 'analyze_and_recover') as mock_analyze, \
             patch.object(self.dispatcher.escalation_engine, 'process_escalation') as mock_process:

            rand_recovery_res = {"status": uuid.uuid4().hex}
            rand_escalation_res = {"status": uuid.uuid4().hex}
            mock_analyze.return_value = rand_recovery_res
            mock_process.return_value = rand_escalation_res

            exc = ValueError(self.rand_error_msg)
            result = self.dispatcher.dispatch_recovery(self.rand_incident_id, self.rand_module_name, exc)

            expected_context = {"incident_id": self.rand_incident_id, "module_name": self.rand_module_name}
            mock_analyze.assert_called_once_with(self.rand_module_name, exc, expected_context)
            mock_process.assert_called_once_with(self.rand_incident_id)

            self.assertEqual(result["incident_id"], self.rand_incident_id)
            self.assertEqual(result["recovery_result"], rand_recovery_res)
            self.assertEqual(result["escalation_result"], rand_escalation_res)
            self.assertEqual(result["status"], "dispatched")


if __name__ == '__main__':
    unittest.main()