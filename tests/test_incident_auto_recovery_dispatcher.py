import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher
from skills.incident_sla_recovery_coordinator import IncidentSlaRecoveryCoordinator


class TestIncidentAutoRecoveryDispatcher(unittest.TestCase):

    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()
        self.rand_str = lambda: uuid.uuid4().hex
        self.rand_num = lambda: random.randint(1000, 99999)

    def test_init_components(self):
        self.assertIsNotNone(self.dispatcher.escalation_engine)
        self.assertIsNotNone(self.dispatcher.recovery_hub)
        self.assertIsInstance(self.dispatcher.sla_coordinator, IncidentSlaRecoveryCoordinator)

    def test_dispatch_escalation(self):
        incident_id = self.rand_str()
        expected_result = {"incident_id": incident_id, "escalated": True, "code": self.rand_num()}

        with patch.object(self.dispatcher.escalation_engine, 'process_escalation', return_value=expected_result) as mock_process:
            result = self.dispatcher.dispatch_escalation(incident_id)
            mock_process.assert_called_once_with(incident_id)
            self.assertEqual(result, expected_result)

    def test_handle_runtime_failure(self):
        module_name = f"module_{self.rand_str()}"
        exc_msg = self.rand_str()
        exception = RuntimeError(exc_msg)
        context = {"token": self.rand_str(), "retry": self.rand_num()}
        expected_analysis = {"status": "analyzed", "module": module_name}

        with patch.object(self.dispatcher.recovery_hub, 'analyze_and_recover', return_value=expected_analysis) as mock_analyze:
            result = self.dispatcher.handle_runtime_failure(module_name, exception, context)
            mock_analyze.assert_called_once_with(module_name, exception, context)
            self.assertEqual(result, expected_analysis)

    def test_run_full_recovery_cycle_success(self):
        module_name = f"mod_{self.rand_str()}"
        exc = Exception(self.rand_str())
        tb_str = "".join(random.choices(string.ascii_letters, k=30))
        incident_id = self.rand_str()
        patch_payload = {"patch_id": self.rand_str(), "data": self.rand_num()}

        with patch.object(self.dispatcher.recovery_hub, 'capture_failure', return_value={"incident_id": incident_id}) as mock_capture, \
             patch.object(self.dispatcher.escalation_engine, 'check_and_trigger_patching', return_value=True) as mock_check, \
             patch.object(self.dispatcher.recovery_hub, 'generate_patch', return_value=patch_payload) as mock_gen, \
             patch.object(self.dispatcher.recovery_hub, 'deploy_and_verify', return_value=True) as mock_deploy, \
             patch.object(self.dispatcher.sla_coordinator, 'coordinate_sla_closure', return_value=True) as mock_sla:

            success = self.dispatcher.run_full_recovery_cycle(module_name, exc, tb_str)

            mock_capture.assert_called_once_with(module_name, exc, tb_str)
            mock_check.assert_called_once()
            mock_gen.assert_called_once_with(incident_id)
            mock_deploy.assert_called_once_with(incident_id, patch_payload)
            mock_sla.assert_called_once_with(incident_id)
            self.assertTrue(success)

    def test_run_full_recovery_cycle_no_patch(self):
        module_name = f"mod_{self.rand_str()}"
        exc = Exception(self.rand_str())
        tb_str = self.rand_str()
        incident_id = self.rand_str()

        with patch.object(self.dispatcher.recovery_hub, 'capture_failure', return_value=incident_id) as mock_capture, \
             patch.object(self.dispatcher.escalation_engine, 'check_and_trigger_patching', return_value=False) as mock_check, \
             patch.object(self.dispatcher.sla_coordinator, 'coordinate_sla_closure') as mock_sla:

            success = self.dispatcher.run_full_recovery_cycle(module_name, exc, tb_str)

            mock_capture.assert_called_once_with(module_name, exc, tb_str)
            mock_check.assert_called_once()
            mock_sla.assert_not_called()
            self.assertFalse(success)

    def test_evaluate_telemetry(self):
        telemetry_data = {"risk_score": random.random(), "anomaly_id": self.rand_str()}

        with patch.object(self.dispatcher.escalation_engine, 'evaluate_system_telemetry_risks', return_value=telemetry_data) as mock_eval:
            result = self.dispatcher.evaluate_telemetry()
            mock_eval.assert_called_once()
            self.assertEqual(result, telemetry_data)

    def test_consume_and_process_stream(self):
        stream_bytes = io.BytesIO(bytes(self.rand_str(), 'utf-8')).read()

        with patch.object(self.dispatcher.escalation_engine, 'consume_stream_data', return_value=stream_bytes) as mock_consume:
            result = self.dispatcher.consume_and_process_stream()
            mock_consume.assert_called_once()
            self.assertEqual(result, stream_bytes)

    def test_dispatch_recovery(self):
        incident_id = self.rand_str()
        module_name = f"module_{self.rand_str()}"
        exc = ValueError(self.rand_str())
        rec_res = {"recovered": True, "id": self.rand_num()}
        esc_res = {"escalated": False, "level": self.rand_num()}
        sla_res = {"sla_maintained": True}

        with patch.object(self.dispatcher.recovery_hub, 'analyze_and_recover', return_value=rec_res) as mock_rec, \
             patch.object(self.dispatcher.escalation_engine, 'process_escalation', return_value=esc_res) as mock_esc, \
             patch.object(self.dispatcher.sla_coordinator, 'coordinate_sla_closure', return_value=sla_res) as mock_sla:

            result = self.dispatcher.dispatch_recovery(incident_id, module_name, exc)

            mock_rec.assert_called_once_with(module_name, exc, {"incident_id": incident_id, "module_name": module_name})
            mock_esc.assert_called_once_with(incident_id)
            mock_sla.assert_called_once_with(incident_id)

            self.assertEqual(result["incident_id"], incident_id)
            self.assertEqual(result["recovery_result"], rec_res)
            self.assertEqual(result["escalation_result"], esc_res)
            self.assertEqual(result["sla_coordination"], sla_res)
            self.assertEqual(result["status"], "dispatched")


if __name__ == '__main__':
    unittest.main()