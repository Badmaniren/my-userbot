import unittest
import uuid
import random
from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher

class TestIncidentAutoRecoveryDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()
        self.random_id = f"inc-{uuid.uuid4()}"
        self.module_name = f"module_{random.randint(1000, 9999)}"
        self.exception_msg = f"Test failure exception {uuid.uuid4()}"

    def test_dispatch_recovery_integration(self):
        exc = RuntimeError(self.exception_msg)
        result = self.dispatcher.dispatch_recovery(
            incident_id=self.random_id,
            module_name=self.module_name,
            exception=exc
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), self.random_id)
        self.assertEqual(result.get("status"), "dispatched")
        self.assertIn("recovery_result", result)
        self.assertIn("escalation_result", result)

    def test_evaluate_telemetry_integration(self):
        telemetry = self.dispatcher.evaluate_telemetry()
        self.assertIsInstance(telemetry, dict)

    def test_consume_and_process_stream_integration(self):
        stream_data = self.dispatcher.consume_and_process_stream()
        self.assertTrue(isinstance(stream_data, bytes) or stream_data is None)

if __name__ == "__main__":
    unittest.main()