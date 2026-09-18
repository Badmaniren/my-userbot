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
        self.incident_id = uuid.uuid4().hex
        self.module_name = "".join(random.choices(string.ascii_lowercase, k=10))
        self.exception = RuntimeError(f"err_{uuid.uuid4().hex}")
        self.traceback_str = f"Traceback (most recent call last):\n  File '{self.module_name}.py', line {random.randint(1, 100)}\n    raise {self.exception.__class__.__name__}"

    def test_dispatch_escalation(self):
        expected_result = {"escalation_status": "processed", "id": self.incident_id}
        with patch.object(self.dispatcher.escalation_engine, "process_escalation", return_value=expected_result) as mock_process:
            result = self.dispatcher.dispatch_escalation(self.incident_id)
            mock_process.assert_called_once_with(self.incident_id)
            self.assertEqual(result, expected_result)

    def test_handle_runtime_failure(self):
        context = {"session_id": uuid.uuid4().hex}
        expected_recovery = {"recovered": True, "module": self.module_name}
        with patch.object(self.dispatcher.recovery_hub, "analyze_and_recover", return_value=expected_recovery) as mock_recover:
            result = self.dispatcher.handle_runtime_failure(self.module_name, self.exception, context)
            mock_recover.assert_called_once_with(self.module_name, self.exception, context)
            self.assertEqual(result, expected_recovery)

    def test_run_full_recovery_cycle_success(self):
        with patch.object(self.dispatcher.recovery_hub, "capture_failure", return_value=self.incident_id) as mock_capture,\
             patch.object(self.dispatcher.escalation_engine, "check_and_trigger_patching", return_value=True) as mock_check,\
             patch.object(self.dispatcher.recovery_hub, "generate_patch", return_value={"patch": uuid.uuid4().hex}) as mock_gen,\
             patch.object(self.dispatcher.recovery_hub, "deploy_and_verify", return_value=True) as mock_deploy,\
             patch.object(self.dispatcher.audit_collector, "record_audit_event") as mock_audit,\
             patch.object(self.dispatcher.health_aggregator, "verify_system_stability") as mock_health:

            success = self.dispatcher.run_full_recovery_cycle(self.module_name, self.exception, self.traceback_str)

            mock_capture.assert_called_once_with(self.module_name, self.exception, self.traceback_str)
            mock_check.assert_called_once()
            mock_gen.assert_called_once_with(self.incident_id)
            mock_deploy.assert_called_once()
            mock_audit.assert_called_once()
            mock_health.assert_called_once()
            self.assertTrue(success)

    def test_run_full_recovery_cycle_no_patch(self):
        with patch.object(self.dispatcher.recovery_hub, "capture_failure", return_value={"incident_id": self.incident_id}) as mock_capture,\
             patch.object(self.dispatcher.escalation_engine, "check_and_trigger_patching", return_value=False) as mock_check,\
             patch.object(self.dispatcher.recovery_hub, "generate_patch") as mock_gen:

            success = self.dispatcher.run_full_recovery_cycle(self.module_name, self.exception, self.traceback_str)

            mock_capture.assert_called_once()
            mock_check.assert_called_once()
            mock_gen.assert_not_called()
            self.assertFalse(success)

    def test_evaluate_telemetry(self):
        telemetry_data = {"risk_level": random.choice(["LOW", "HIGH", "CRITICAL"]), "score": random.random()}
        with patch.object(self.dispatcher.escalation_engine, "evaluate_system_telemetry_risks", return_value=telemetry_data) as mock_eval:
            result = self.dispatcher.evaluate_telemetry()
            mock_eval.assert_called_once()
            self.assertEqual(result, telemetry_data)

    def test_consume_and_process_stream(self):
        stream_bytes = uuid.uuid4().hex.encode('utf-8')
        with patch.object(self.dispatcher.escalation_engine, "consume_stream_data", return_value=stream_bytes) as mock_consume:
            result = self.dispatcher.consume_and_process_stream()
            mock_consume.assert_called_once()
            self.assertEqual(result, stream_bytes)

    def test_dispatch_recovery(self):
        recovery_ret = {"action": uuid.uuid4().hex}
        escalation_ret = {"status": uuid.uuid4().hex}
        with patch.object(self.dispatcher.recovery_hub, "analyze_and_recover", return_value=recovery_ret) as mock_recover,\
             patch.object(self.dispatcher.escalation_engine, "process_escalation", return_value=escalation_ret) as mock_escalate,\
             patch.object(self.dispatcher.audit_collector, "record_audit_event") as mock_audit:

            result = self.dispatcher.dispatch_recovery(self.incident_id, self.module_name, self.exception)

            mock_recover.assert_called_once()
            mock_escalate.assert_called_once_with(self.incident_id)
            mock_audit.assert_called_once()

            self.assertEqual(result["incident_id"], self.incident_id)
            self.assertEqual(result["recovery_result"], recovery_ret)
            self.assertEqual(result["escalation_result"], escalation_ret)
            self.assertEqual(result["status"], "dispatched")


if __name__ == "__main__":
    unittest.main()