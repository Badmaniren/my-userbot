import unittest
import uuid
import random
from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher


class TestIncidentAutoRecoveryDispatcherIntegration(unittest.TestCase):

    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()
        self.test_incident_id = f"inc-{uuid.uuid4()}"
        self.test_module_name = f"module_{random.randint(1000, 9999)}"
        self.test_exception = RuntimeError(f"Simulated failure {random.randint(1, 100)}")
        self.test_traceback = f"Traceback (most recent call last):\n  File '{self.test_module_name}.py', line {random.randint(1, 50)}, in <module>\n    raise Exception()\n{type(self.test_exception).__name__}: {str(self.test_exception)}"

    def test_dispatch_recovery_integration(self):
        result = self.dispatcher.dispatch_recovery(
            self.test_incident_id, 
            self.test_module_name, 
            self.test_exception
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), self.test_incident_id)
        self.assertEqual(result.get("status"), "dispatched")
        self.assertIn("recovery_result", result)
        self.assertIn("escalation_result", result)

    def test_run_full_recovery_cycle_integration(self):
        cycle_result = self.dispatcher.run_full_recovery_cycle(
            self.test_module_name, 
            self.test_exception, 
            self.test_traceback
        )

        self.assertIsInstance(cycle_result, bool)

    def test_evaluate_telemetry_integration(self):
        telemetry = self.dispatcher.evaluate_telemetry()
        self.assertIsInstance(telemetry, (dict, list, type(None)))

    def test_consume_and_process_stream_integration(self):
        stream_data = self.dispatcher.consume_and_process_stream()
        self.assertIsInstance(stream_data, (bytes, str, type(None)))


if __name__ == "__main__":
    unittest.main()