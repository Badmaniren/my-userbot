import unittest
import uuid
import random
from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher


class TestIncidentAutoRecoveryDispatcherIntegration(unittest.TestCase):

    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()
        self.random_incident_id = f"inc-{uuid.uuid4()}"
        self.random_module_name = f"module_{random.randint(1000, 9999)}"
        self.test_exception = RuntimeError(f"Simulated failure {uuid.uuid4()}")
        self.traceback_sample = "Traceback (most recent call last):\n  File 'test.py', line 1, in <module>\n    raise RuntimeError()"

    def test_dispatch_recovery_integration(self):
        result = self.dispatcher.dispatch_recovery(
            incident_id=self.random_incident_id,
            module_name=self.random_module_name,
            exception=self.test_exception
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), self.random_incident_id)
        self.assertIn("recovery_result", result)
        self.assertIn("escalation_result", result)
        self.assertEqual(result.get("status"), "dispatched")

    def test_run_full_recovery_cycle_integration(self):
        success = self.dispatcher.run_full_recovery_cycle(
            module_name=self.random_module_name,
            exception=self.test_exception,
            traceback_str=self.traceback_sample
        )
        self.assertIsInstance(success, bool)

    def test_handle_runtime_failure_integration(self):
        context = {"run_id": str(uuid.uuid4()), "attempt": random.randint(1, 5)}
        recovery_response = self.dispatcher.handle_runtime_failure(
            module_name=self.random_module_name,
            exception=self.test_exception,
            context=context
        )
        self.assertIsNotNone(recovery_response)

    def test_evaluate_telemetry_integration(self):
        telemetry = self.dispatcher.evaluate_telemetry()
        self.assertIsInstance(telemetry, (dict, list, type(None)))


if __name__ == "__main__":
    unittest.main()