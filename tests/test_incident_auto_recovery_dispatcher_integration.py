import unittest
import uuid
import random
from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher


class TestIncidentAutoRecoveryDispatcherIntegration(unittest.TestCase):

    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()
        self.test_incident_id = f"inc-{uuid.uuid4()}"
        self.test_module_name = f"mod_{uuid.uuid4().hex[:8]}"
        self.test_error_message = f"Runtime failure in module {uuid.uuid4()}"
        self.test_exception = RuntimeError(self.test_error_message)
        self.test_traceback = f"Traceback (most recent call last):\n  File '{self.test_module_name}.py', line {random.randint(1, 100)}, in <module>\n    raise RuntimeError('{self.test_error_message}')"

    def test_full_recovery_cycle_integration(self):
        result = self.dispatcher.run_full_recovery_cycle(
            self.test_module_name, 
            self.test_exception, 
            self.test_traceback
        )
        self.assertIsInstance(result, bool)

    def test_dispatch_recovery_integration(self):
        recovery_response = self.dispatcher.dispatch_recovery(
            self.test_incident_id, 
            self.test_module_name, 
            self.test_exception
        )
        
        self.assertIsInstance(recovery_response, dict)
        self.assertEqual(recovery_response.get("incident_id"), self.test_incident_id)
        self.assertEqual(recovery_response.get("status"), "dispatched")
        self.assertIn("recovery_result", recovery_response)
        self.assertIn("escalation_result", recovery_response)

    def test_evaluate_telemetry_integration(self):
        telemetry_risks = self.dispatcher.evaluate_telemetry()
        self.assertIsInstance(telemetry_risks, (dict, list, type(None)))

    def test_consume_and_process_stream_integration(self):
        stream_data = self.dispatcher.consume_and_process_stream()
        self.assertIsInstance(stream_data, bytes)


if __name__ == "__main__":
    unittest.main()