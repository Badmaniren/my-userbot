import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import sys

from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher

class TestIncidentAutoRecoveryDispatcher(unittest.TestCase):

    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()
        self.rand_incident_id = uuid.uuid4().hex
        self.rand_module_name = f"mod_{uuid.uuid4().hex[:8]}"
        self.rand_traceback = f"Traceback (most recent call last):\n  File \"{self.rand_module_name}.py\", line {random.randint(1, 100)}\n    raise RuntimeError(\"{uuid.uuid4().hex}\")"
        self.rand_exception = RuntimeError(uuid.uuid4().hex)

    def test_init_composition(self):
        self.assertIsNotNone(self.dispatcher.escalation_engine)
        self.assertIsNotNone(self.dispatcher.recovery_hub)

    def test_dispatch_escalation(self):
        expected_result = {"status": "escalated", "id": self.rand_incident_id}
        with patch.object(self.dispatcher.escalation_engine, 'process_escalation', return_value=expected_result) as mock_process:
            result = self.dispatcher.dispatch_escalation(self.rand_incident_id)
            mock_process.assert_called_once_with(self.rand_incident_id)
            self.assertEqual(result, expected_result)

    def test_handle_runtime_failure(self):
        context = {"meta": uuid.uuid4().hex}
        expected_result = {"recovered": True, "incident": self.rand_incident_id}
        with patch.object(self.dispatcher.recovery_hub, 'analyze_and_recover', return_value=expected_result) as mock_analyze:
            result = self.dispatcher.handle_runtime_failure(self.rand_module_name, self.rand_exception, context)
            mock_analyze.assert_called_once_with(self.rand_module_name, self.rand_exception, context)
            self.assertEqual(result, expected_result)

    def test_run_full_recovery_cycle_success(self):
        patch_payload = {"patch_code": uuid.uuid4().hex}
        with patch.object(self.dispatcher.recovery_hub, 'capture_failure', return_value=self.rand_incident_id) as mock_capture, \
             patch.object(self.dispatcher.escalation_engine, 'check_and_trigger_patching', return_value=True) as mock_check, \
             patch.object(self.dispatcher.recovery_hub, 'generate_patch', return_value=patch_payload) as mock_gen, \
             patch.object(self.dispatcher.recovery_hub, 'deploy_and_verify', return_value=True) as mock_deploy:

            result = self.dispatcher.run_full_recovery_cycle(self.rand_module_name, self.rand_exception, self.rand_traceback)
            
            mock_capture.assert_called_once_with(self.rand_module_name, self.rand_exception, self.rand_traceback)
            mock_check.assert_called_once()
            mock_gen.assert_called_once_with(self.rand_incident_id)
            mock_deploy.assert_called_once_with(self.rand_incident_id, patch_payload)
            self.assertTrue(result)

    def test_run_full_recovery_cycle_dict_incident_id(self):
        incident_dict = {"incident_id": self.rand_incident_id}
        patch_payload = {"patch_code": uuid.uuid4().hex}
        with patch.object(self.dispatcher.recovery_hub, 'capture_failure', return_value=incident_dict) as mock_capture, \
             patch.object(self.dispatcher.escalation_engine, 'check_and_trigger_patching', return_value=True) as mock_check, \
             patch.object(self.dispatcher.recovery_hub, 'generate_patch', return_value=patch_payload) as mock_gen, \
             patch.object(self.dispatcher.recovery_hub, 'deploy_and_verify', return_value=True) as mock_deploy:

            result = self.dispatcher.run_full_recovery_cycle(self.rand_module_name, self.rand_exception, self.rand_traceback)
            
            mock_gen.assert_called_once_with(self.rand_incident_id)
            self.assertTrue(result)

    def test_run_full_recovery_cycle_no_patch(self):
        with patch.object(self.dispatcher.recovery_hub, 'capture_failure', return_value=self.rand_incident_id) as mock_capture, \
             patch.object(self.dispatcher.escalation_engine, 'check_and_trigger_patching', return_value=False) as mock_check, \
             patch.object(self.dispatcher.recovery_hub, 'generate_patch') as mock_gen:

            result = self.dispatcher.run_full_recovery_cycle(self.rand_module_name, self.rand_exception, self.rand_traceback)
            
            mock_capture.assert_called_once_with(self.rand_module_name, self.rand_exception, self.rand_traceback)
            mock_check.assert_called_once()
            mock_gen.assert_not_called()
            self.assertFalse(result)

    def test_evaluate_telemetry(self):
        telemetry_data = {"risk_level": random.choice(["low", "medium", "high"]), "score": random.random()}
        with patch.object(self.dispatcher.escalation_engine, 'evaluate_system_telemetry_risks', return_value=telemetry_data) as mock_eval:
            result = self.dispatcher.evaluate_telemetry()
            mock_eval.assert_called_once()
            self.assertEqual(result, telemetry_data)

    def test_consume_and_process_stream(self):
        stream_bytes = uuid.uuid4().hex.encode('utf-8')
        with patch.object(self.dispatcher.escalation_engine, 'consume_stream_data', return_value=stream_bytes) as mock_consume:
            result = self.dispatcher.consume_and_process_stream()
            mock_consume.assert_called_once()
            self.assertEqual(result, stream_bytes)

    def test_dispatch_recovery(self):
        rec_res = {"recovered": True, "detail": uuid.uuid4().hex}
        esc_res = {"escalated": False, "reason": uuid.uuid4().hex}

        with patch.object(self.dispatcher.recovery_hub, 'analyze_and_recover', return_value=rec_res) as mock_rec, \
             patch.object(self.dispatcher.escalation_engine, 'process_escalation', return_value=esc_res) as mock_esc:

            result = self.dispatcher.dispatch_recovery(self.rand_incident_id, self.rand_module_name, self.rand_exception)

            mock_rec.assert_called_once_with(
                self.rand_module_name, 
                self.rand_exception, 
                {"incident_id": self.rand_incident_id, "module_name": self.rand_module_name}
            )
            mock_esc.assert_called_once_with(self.rand_incident_id)

            self.assertEqual(result["incident_id"], self.rand_incident_id)
            self.assertEqual(result["recovery_result"], rec_res)
            self.assertEqual(result["escalation_result"], esc_res)
            self.assertEqual(result["status"], "dispatched")

if __name__ == '__main__':
    unittest.main()