import unittest
import uuid
import random
from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher


class TestIncidentAutoRecoveryDispatcherIntegration(unittest.TestCase):

    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()
        self.random_incident_id = f"inc-{uuid.uuid4()}"
        self.random_module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.random_error_message = f"Runtime failure at {random.randint(1000, 9999)}"

    def test_full_recovery_cycle_integration(self):
        exception_instance = RuntimeError(self.random_error_message)
        traceback_info = f"Traceback (most recent call last):\n  File '{self.random_module_name}.py', line 1, in <module>\n    raise RuntimeError('{self.random_error_message}')"

        result = self.dispatcher.run_full_recovery_cycle(
            module_name=self.random_module_name,
            exception=exception_instance,
            traceback_str=traceback_info
        )

        self.assertIsInstance(result, bool)

    def test_dispatch_recovery_integration(self):
        exception_instance = ValueError(self.random_error_message)

        response = self.dispatcher.dispatch_recovery(
            incident_id=self.random_incident_id,
            module_name=self.random_module_name,
            exception=exception_instance
        )

        self.assertIsInstance(response, dict)
        self.assertIn("incident_id", response)
        self.assertEqual(response["incident_id"], self.random_incident_id)
        self.assertIn("recovery_result", response)
        self.assertIn("escalation_result", response)
        self.assertEqual(response.get("status"), "dispatched")

    def test_evaluate_telemetry_integration(self):
        telemetry_data = self.dispatcher.evaluate_telemetry()
        self.assertIsInstance(telemetry_data, dict)

    def test_consume_and_process_stream_integration(self):
        stream_data = self.dispatcher.consume_and_process_stream()
        self.assertIsInstance(stream_data, bytes)


if __name__ == "__main__":
    unittest.main()