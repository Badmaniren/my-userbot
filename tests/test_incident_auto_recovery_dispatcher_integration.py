import unittest
import uuid
import random
from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher


class TestIncidentAutoRecoveryDispatcherIntegration(unittest.TestCase):

    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()
        self.module_name = f"test_module_{uuid.uuid4().hex[:8]}"
        self.incident_id = f"INC-{random.randint(10000, 99999)}"
        self.test_exception = RuntimeError(f"Simulated failure: {uuid.uuid4().hex}")
        self.traceback_str = f"Traceback (most recent call last):\n  File '{self.module_name}.py', line {random.randint(1, 100)}\n    raise Exception\n{type(self.test_exception).__name__}: {str(self.test_exception)}"

    def test_run_full_recovery_cycle_integration(self):
        result = self.dispatcher.run_full_recovery_cycle(
            module_name=self.module_name,
            exception=self.test_exception,
            traceback_str=self.traceback_str
        )
        self.assertIsInstance(result, bool)

    def test_dispatch_recovery_integration(self):
        response = self.dispatcher.dispatch_recovery(
            incident_id=self.incident_id,
            module_name=self.module_name,
            exception=self.test_exception
        )
        
        self.assertIsInstance(response, dict)
        self.assertEqual(response.get("incident_id"), self.incident_id)
        self.assertEqual(response.get("status"), "dispatched")
        self.assertIn("recovery_result", response)
        self.assertIn("escalation_result", response)

    def test_evaluate_telemetry_integration(self):
        telemetry = self.dispatcher.evaluate_telemetry()
        self.assertIsInstance(telemetry, (dict, list, type(None)))

    def test_consume_and_process_stream_integration(self):
        stream_data = self.dispatcher.consume_and_process_stream()
        self.assertIsInstance(stream_data, (bytes, str, type(None)))


if __name__ == "__main__":
    unittest.main()