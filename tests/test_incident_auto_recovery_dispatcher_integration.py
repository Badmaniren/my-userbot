import unittest
import uuid
import random
from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine
from skills.error_recovery_hub import ErrorRecoveryHub


class TestIncidentAutoRecoveryDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()
        self.random_str = str(uuid.uuid4())
        self.incident_id = f"inc-{self.random_str[:8]}"
        self.module_name = f"module_{random.randint(1000, 9999)}"
        self.test_exception = RuntimeError(f"Simulated failure {random.randint(1, 100)}.")
        self.context = {"env": "integration_test", "uuid": self.random_str}

    def test_full_recovery_cycle_integration(self):
        traceback_str = f"Traceback (most recent call last):\n  File '{self.module_name}.py', line 1, in <module>\n    raise Exception()\nException: test"
        
        result = self.dispatcher.run_full_recovery_cycle(
            self.module_name, 
            self.test_exception, 
            traceback_str
        )
        self.assertIsInstance(result, bool)

    def test_dispatch_recovery_integration(self):
        result = self.dispatcher.dispatch_recovery(
            self.incident_id,
            self.module_name,
            self.test_exception
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), self.incident_id)
        self.assertEqual(result.get("status"), "dispatched")
        self.assertIn("recovery_result", result)
        self.assertIn("escalation_result", result)

    def test_evaluate_telemetry_and_stream(self):
        telemetry = self.dispatcher.evaluate_telemetry()
        self.assertIsInstance(telemetry, (dict, list, type(None)))

        stream_data = self.dispatcher.consume_and_process_stream()
        self.assertIsInstance(stream_data, (bytes, str, type(None)))

    def test_handle_runtime_failure_integration(self):
        recovery_response = self.dispatcher.handle_runtime_failure(
            self.module_name,
            self.test_exception,
            self.context
        )
        self.assertIsNotNone(recovery_response)


if __name__ == "__main__":
    unittest.main()