import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher


class TestIncidentAutoRecoveryDispatcher(unittest.TestCase):

    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()

    def test_dispatch_escalation(self):
        rand_incident = uuid.uuid4().hex
        expected_result = {"status": uuid.uuid4().hex, "incident_id": rand_incident}

        with patch.object(self.dispatcher.escalation_engine, 'process_escalation', return_value=expected_result) as mock_process:
            result = self.dispatcher.dispatch_escalation(rand_incident)
            
            mock_process.assert_called_once_with(rand_incident)
            self.assertEqual(result, expected_result)

    def test_handle_runtime_failure(self):
        rand_module = uuid.uuid4().hex
        rand_msg = uuid.uuid4().hex
        rand_exc = RuntimeError(rand_msg)
        rand_context = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_response = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch.object(self.dispatcher.recovery_hub, 'analyze_and_recover', return_value=expected_response) as mock_analyze:
            result = self.dispatcher.handle_runtime_failure(rand_module, rand_exc, rand_context)
            
            mock_analyze.assert_called_once_with(rand_module, rand_exc, rand_context)
            self.assertEqual(result, expected_response)

    def test_run_full_recovery_cycle_success(self):
        rand_module = uuid.uuid4().hex
        rand_exc = Exception(uuid.uuid4().hex)
        rand_traceback = uuid.uuid4().hex
        rand_incident_id = uuid.uuid4().hex
        rand_patch = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.dispatcher.recovery_hub, 'capture_failure', return_value=rand_incident_id) as mock_capture, \
             patch.object(self.dispatcher.escalation_engine, 'check_and_trigger_patching', return_value=True) as mock_check, \
             patch.object(self.dispatcher.recovery_hub, 'generate_patch', return_value=rand_patch) as mock_generate, \
             patch.object(self.dispatcher.recovery_hub, 'deploy_and_verify', return_value=True) as mock_deploy:

            success = self.dispatcher.run_full_recovery_cycle(rand_module, rand_exc, rand_traceback)

            mock_capture.assert_called_once_with(rand_module, rand_exc, rand_traceback)
            mock_check.assert_called_once()
            mock_generate.assert_called_once_with(rand_incident_id)
            mock_deploy.assert_called_once_with(rand_incident_id, rand_patch)
            self.assertTrue(success)

    def test_run_full_recovery_cycle_dict_incident_id(self):
        rand_module = uuid.uuid4().hex
        rand_exc = Exception(uuid.uuid4().hex)
        rand_traceback = uuid.uuid4().hex
        rand_incident_id = uuid.uuid4().hex
        incident_dict = {"incident_id": rand_incident_id}
        rand_patch = uuid.uuid4().hex

        with patch.object(self.dispatcher.recovery_hub, 'capture_failure', return_value=incident_dict) as mock_capture, \
             patch.object(self.dispatcher.escalation_engine, 'check_and_trigger_patching', return_value=True) as mock_check, \
             patch.object(self.dispatcher.recovery_hub, 'generate_patch', return_value=rand_patch) as mock_generate, \
             patch.object(self.dispatcher.recovery_hub, 'deploy_and_verify', return_value=True) as mock_deploy:

            success = self.dispatcher.run_full_recovery_cycle(rand_module, rand_exc, rand_traceback)

            mock_generate.assert_called_once_with(rand_incident_id)
            self.assertTrue(success)

    def test_run_full_recovery_cycle_no_patch_needed(self):
        rand_module = uuid.uuid4().hex
        rand_exc = Exception(uuid.uuid4().hex)
        rand_traceback = uuid.uuid4().hex
        rand_incident_id = uuid.uuid4().hex

        with patch.object(self.dispatcher.recovery_hub, 'capture_failure', return_value=rand_incident_id) as mock_capture, \
             patch.object(self.dispatcher.escalation_engine, 'check_and_trigger_patching', return_value=False) as mock_check:

            success = self.dispatcher.run_full_recovery_cycle(rand_module, rand_exc, rand_traceback)

            mock_capture.assert_called_once_with(rand_module, rand_exc, rand_traceback)
            mock_check.assert_called_once()
            self.assertFalse(success)

    def test_evaluate_telemetry(self):
        expected_telemetry = {uuid.uuid4().hex: random.random()}

        with patch.object(self.dispatcher.escalation_engine, 'evaluate_system_telemetry_risks', return_value=expected_telemetry) as mock_eval:
            result = self.dispatcher.evaluate_telemetry()
            
            mock_eval.assert_called_once()
            self.assertEqual(result, expected_telemetry)

    def test_consume_and_process_stream(self):
        rand_bytes = "".join(random.choices(string.printable, k=32)).encode('utf-8')

        with patch.object(self.dispatcher.escalation_engine, 'consume_stream_data', return_value=rand_bytes) as mock_consume:
            result = self.dispatcher.consume_and_process_stream()

            mock_consume.assert_called_once()
            self.assertEqual(result, rand_bytes)
            
            stream_bytes = io.BytesIO(result).read()
            self.assertEqual(stream_bytes, rand_bytes)

    def test_dispatch_recovery(self):
        rand_incident = uuid.uuid4().hex
        rand_module = uuid.uuid4().hex
        rand_exc = Exception(uuid.uuid4().hex)
        expected_recovery_res = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_escalation_res = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.dispatcher.recovery_hub, 'analyze_and_recover', return_value=expected_recovery_res) as mock_analyze, \
             patch.object(self.dispatcher.escalation_engine, 'process_escalation', return_value=expected_escalation_res) as mock_process:

            result = self.dispatcher.dispatch_recovery(rand_incident, rand_module, rand_exc)

            mock_analyze.assert_called_once_with(rand_module, rand_exc, {"incident_id": rand_incident, "module_name": rand_module})
            mock_process.assert_called_once_with(rand_incident)
            
            self.assertEqual(result["incident_id"], rand_incident)
            self.assertEqual(result["recovery_result"], expected_recovery_res)
            self.assertEqual(result["escalation_result"], expected_escalation_res)
            self.assertEqual(result["status"], "dispatched")


if __name__ == '__main__':
    unittest.main()