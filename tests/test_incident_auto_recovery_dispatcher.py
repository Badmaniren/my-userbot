import unittest
from unittest.mock import patch
import random
import uuid
import string
from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher


class TestIncidentAutoRecoveryDispatcher(unittest.TestCase):

    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()

    def test_dispatch_escalation_success(self):
        random_incident_id = uuid.uuid4().hex
        expected_result = {"status": "escalated", "ref": uuid.uuid4().hex}

        with patch("skills.incident_auto_escalation_engine.IncidentAutoEscalationEngine.process_escalation", return_value=expected_result) as mock_process:
            result = self.dispatcher.dispatch_escalation(random_incident_id)
            mock_process.assert_called_once_with(random_incident_id)
            self.assertEqual(result, expected_result)

    def test_handle_runtime_failure_success(self):
        random_module = ''.join(random.choices(string.ascii_lowercase, k=10))
        random_exc = RuntimeError(''.join(random.choices(string.ascii_letters, k=15)))
        random_context = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_analysis = {"recovered": True, "details": uuid.uuid4().hex}

        with patch("skills.error_recovery_hub.ErrorRecoveryHub.analyze_and_recover", return_value=expected_analysis) as mock_analyze:
            result = self.dispatcher.handle_runtime_failure(random_module, random_exc, random_context)
            mock_analyze.assert_called_once_with(random_module, random_exc, random_context)
            self.assertEqual(result, expected_analysis)

    def test_run_full_recovery_cycle_success(self):
        random_module = ''.join(random.choices(string.ascii_lowercase, k=8))
        random_exc = ValueError(''.join(random.choices(string.ascii_letters, k=10)))
        random_traceback = ''.join(random.choices(string.printable, k=30))
        random_incident_id = uuid.uuid4().hex
        random_payload = {"patch_data": uuid.uuid4().hex}

        with patch("skills.error_recovery_hub.ErrorRecoveryHub.capture_failure", return_value=random_incident_id) as mock_capture,\
             patch("skills.incident_auto_escalation_engine.IncidentAutoEscalationEngine.check_and_trigger_patching", return_value=True) as mock_check,\
             patch("skills.error_recovery_hub.ErrorRecoveryHub.generate_patch", return_value=random_payload) as mock_gen,\
             patch("skills.error_recovery_hub.ErrorRecoveryHub.deploy_and_verify", return_value=True) as mock_deploy:

            success = self.dispatcher.run_full_recovery_cycle(random_module, random_exc, random_traceback)

            mock_capture.assert_called_once_with(random_module, random_exc, random_traceback)
            mock_check.assert_called_once()
            mock_gen.assert_called_once_with(random_incident_id)
            mock_deploy.assert_called_once_with(random_incident_id, random_payload)
            self.assertTrue(success)

    def test_run_full_recovery_cycle_dict_incident_id(self):
        random_module = ''.join(random.choices(string.ascii_lowercase, k=9))
        random_exc = TypeError(''.join(random.choices(string.ascii_letters, k=12)))
        random_traceback = ''.join(random.choices(string.printable, k=20))
        random_incident_dict = {"incident_id": uuid.uuid4().hex}
        random_payload = {"patch_data": uuid.uuid4().hex}

        with patch("skills.error_recovery_hub.ErrorRecoveryHub.capture_failure", return_value=random_incident_dict) as mock_capture,\
             patch("skills.incident_auto_escalation_engine.IncidentAutoEscalationEngine.check_and_trigger_patching", return_value=True) as mock_check,\
             patch("skills.error_recovery_hub.ErrorRecoveryHub.generate_patch", return_value=random_payload) as mock_gen,\
             patch("skills.error_recovery_hub.ErrorRecoveryHub.deploy_and_verify", return_value=True) as mock_deploy:

            success = self.dispatcher.run_full_recovery_cycle(random_module, random_exc, random_traceback)

            mock_capture.assert_called_once_with(random_module, random_exc, random_traceback)
            mock_gen.assert_called_once_with(random_incident_dict["incident_id"])
            self.assertTrue(success)

    def test_run_full_recovery_cycle_no_patch(self):
        random_module = ''.join(random.choices(string.ascii_lowercase, k=7))
        random_exc = KeyError(''.join(random.choices(string.ascii_letters, k=8)))
        random_traceback = ''.join(random.choices(string.printable, k=15))
        random_incident_id = uuid.uuid4().hex

        with patch("skills.error_recovery_hub.ErrorRecoveryHub.capture_failure", return_value=random_incident_id) as mock_capture,\
             patch("skills.incident_auto_escalation_engine.IncidentAutoEscalationEngine.check_and_trigger_patching", return_value=False) as mock_check:

            success = self.dispatcher.run_full_recovery_cycle(random_module, random_exc, random_traceback)

            mock_capture.assert_called_once_with(random_module, random_exc, random_traceback)
            mock_check.assert_called_once()
            self.assertFalse(success)

    def test_evaluate_telemetry(self):
        expected_telemetry = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch("skills.incident_auto_escalation_engine.IncidentAutoEscalationEngine.evaluate_system_telemetry_risks", return_value=expected_telemetry) as mock_eval:
            result = self.dispatcher.evaluate_telemetry()
            mock_eval.assert_called_once()
            self.assertEqual(result, expected_telemetry)

    def test_consume_and_process_stream_string(self):
        random_str = ''.join(random.choices(string.ascii_letters, k=20))
        expected_bytes = random_str.encode('utf-8')

        with patch("skills.incident_auto_escalation_engine.IncidentAutoEscalationEngine.consume_stream_data", return_value=random_str) as mock_consume:
            result = self.dispatcher.consume_and_process_stream()
            mock_consume.assert_called_once()
            self.assertEqual(result, expected_bytes)

    def test_consume_and_process_stream_bytes(self):
        expected_bytes = uuid.uuid4().bytes

        with patch("skills.incident_auto_escalation_engine.IncidentAutoEscalationEngine.consume_stream_data", return_value=expected_bytes) as mock_consume:
            result = self.dispatcher.consume_and_process_stream()
            mock_consume.assert_called_once()
            self.assertEqual(result, expected_bytes)

    def test_consume_and_process_stream_list(self):
        random_list = [random.randint(0, 255) for _ in range(10)]
        expected_bytes = bytes(random_list)

        with patch("skills.incident_auto_escalation_engine.IncidentAutoEscalationEngine.consume_stream_data", return_value=random_list) as mock_consume:
            result = self.dispatcher.consume_and_process_stream()
            mock_consume.assert_called_once()
            self.assertEqual(result, expected_bytes)

    def test_consume_and_process_stream_other(self):
        with patch("skills.incident_auto_escalation_engine.IncidentAutoEscalationEngine.consume_stream_data", return_value=None) as mock_consume:
            result = self.dispatcher.consume_and_process_stream()
            mock_consume.assert_called_once()
            self.assertEqual(result, b"")

    def test_dispatch_recovery(self):
        random_incident_id = uuid.uuid4().hex
        random_module = ''.join(random.choices(string.ascii_lowercase, k=11))
        random_exc = Exception(''.join(random.choices(string.ascii_letters, k=10)))
        expected_recovery_res = {"recovered": random.choice([True, False])}
        expected_escalation_res = {"escalated": random.choice([True, False])}

        with patch("skills.error_recovery_hub.ErrorRecoveryHub.analyze_and_recover", return_value=expected_recovery_res) as mock_analyze,\
             patch("skills.incident_auto_escalation_engine.IncidentAutoEscalationEngine.process_escalation", return_value=expected_escalation_res) as mock_process:

            result = self.dispatcher.dispatch_recovery(random_incident_id, random_module, random_exc)

            mock_analyze.assert_called_once_with(random_module, random_exc, {"incident_id": random_incident_id, "module_name": random_module})
            mock_process.assert_called_once_with(random_incident_id)
            self.assertEqual(result, {
                "incident_id": random_incident_id,
                "recovery_result": expected_recovery_res,
                "escalation_result": expected_escalation_res,
                "status": "dispatched"
            })


if __name__ == '__main__':
    unittest.main()