import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher

class TestIncidentAutoRecoveryDispatcher(unittest.TestCase):

    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()

    def test_dispatch_escalation_logic(self):
        random_id = uuid.uuid4().hex
        expected_result = {"status": "escalated", "ref": uuid.uuid4().hex}
        
        with patch.object(self.dispatcher.escalation_engine, 'process_escalation', return_value=expected_result) as mock_method:
            result = self.dispatcher.dispatch_escalation(random_id)
            mock_method.assert_called_once_with(random_id)
            self.assertEqual(result, expected_result)

    def test_handle_runtime_failure_integration(self):
        module = ''.join(random.choices(string.ascii_lowercase, k=10))
        exc = Exception(uuid.uuid4().hex)
        ctx = {"trace": uuid.uuid4().hex}
        expected_recovery = {"recovered": True, "code": random.randint(100, 999)}

        with patch.object(self.dispatcher.recovery_hub, 'analyze_and_recover', return_value=expected_recovery) as mock_hub:
            result = self.dispatcher.handle_runtime_failure(module, exc, ctx)
            mock_hub.assert_called_once_with(module, exc, ctx)
            self.assertEqual(result, expected_recovery)

    def test_run_full_recovery_cycle_success_path(self):
        module = uuid.uuid4().hex
        exc = Exception("Critical Failure")
        trace = uuid.uuid4().hex
        incident_id = uuid.uuid4().hex
        patch_payload = {"patch_id": uuid.uuid4().hex}

        with patch.object(self.dispatcher.recovery_hub, 'capture_failure', return_value=incident_id) as mock_capture:
            with patch.object(self.dispatcher.escalation_engine, 'check_and_trigger_patching', return_value=True) as mock_check:
                with patch.object(self.dispatcher.recovery_hub, 'generate_patch', return_value=patch_payload) as mock_gen:
                    with patch.object(self.dispatcher.recovery_hub, 'deploy_and_verify', return_value=True) as mock_deploy:
                        
                        result = self.dispatcher.run_full_recovery_cycle(module, exc, trace)
                        
                        self.assertTrue(result)
                        mock_capture.assert_called_once_with(module, exc, trace)
                        mock_deploy.assert_called_once_with(incident_id, patch_payload)

    def test_consume_and_process_stream_returns_bytes(self):
        random_bytes = uuid.uuid4().bytes
        
        with patch.object(self.dispatcher.escalation_engine, 'consume_stream_data', return_value=random_bytes) as mock_stream:
            result = self.dispatcher.consume_and_process_stream()
            self.assertEqual(result, random_bytes)
            mock_stream.assert_called_once()

    def test_dispatch_recovery_complex_flow(self):
        incident_id = uuid.uuid4().hex
        module = uuid.uuid4().hex
        exc = Exception(uuid.uuid4().hex)
        
        recovery_resp = {"status": "fixed"}
        escalation_resp = {"status": "notified"}

        with patch.object(self.dispatcher.recovery_hub, 'analyze_and_recover', return_value=recovery_resp) as mock_rec:
            with patch.object(self.dispatcher.escalation_engine, 'process_escalation', return_value=escalation_resp) as mock_esc:
                
                result = self.dispatcher.dispatch_recovery(incident_id, module, exc)
                
                self.assertEqual(result["incident_id"], incident_id)
                self.assertEqual(result["recovery_result"], recovery_resp)
                self.assertEqual(result["escalation_result"], escalation_resp)
                self.assertEqual(result["status"], "dispatched")
                
                mock_rec.assert_called_once()
                mock_esc.assert_called_once_with(incident_id)

    def test_run_full_recovery_cycle_dict_handling(self):
        # Проверка обработки, если capture_failure возвращает словарь
        module = uuid.uuid4().hex
        exc = Exception("Fail")
        trace = uuid.uuid4().hex
        incident_id = uuid.uuid4().hex
        
        with patch.object(self.dispatcher.recovery_hub, 'capture_failure', return_value={"incident_id": incident_id}):
            with patch.object(self.dispatcher.escalation_engine, 'check_and_trigger_patching', return_value=False):
                result = self.dispatcher.run_full_recovery_cycle(module, exc, trace)
                self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()