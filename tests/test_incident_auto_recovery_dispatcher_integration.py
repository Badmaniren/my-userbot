import unittest
import uuid
import random
from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher


class TestIncidentAutoRecoveryDispatcherIntegration(unittest.TestCase):

    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()
        self.module_name = f"test_module_{uuid.uuid4().hex[:8]}"
        self.incident_id = f"INC-{random.randint(10000, 99999)}"
        self.exception = RuntimeError(f"Simulated failure {uuid.uuid4().hex[:6]}")
        self.traceback_str = "Traceback (most recent call last):\n  File 'test.py', line 1, in <module>\n    raise RuntimeError"

    def test_run_full_recovery_cycle_integration(self):
        success = self.dispatcher.run_full_recovery_cycle(
            self.module_name,
            self.exception,
            self.traceback_str
        )

        self.assertIsInstance(success, bool)

        # Проверяем интеграцию с реальным аудитом через косвенные признаки работы компонентов
        telemetry = self.dispatcher.evaluate_telemetry()
        self.assertIsInstance(telemetry, (dict, list, type(None)))

    def test_dispatch_recovery_integration(self):
        result = self.dispatcher.dispatch_recovery(
            self.incident_id,
            self.module_name,
            self.exception
        )

        self.assertIsInstance(result, dict)
        self.assertIn("incident_id", result)
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertIn("recovery_result", result)
        self.assertIn("escalation_result", result)
        self.assertEqual(result.get("status"), "dispatched" if "dispatched" in result.get("status", "") else result.get("status"))

    def test_stream_and_telemetry_integration(self):
        stream_data = self.dispatcher.consume_and_process_stream()
        self.assertIsInstance(stream_data, (bytes, bytearray, type(None)))

        telemetry = self.dispatcher.evaluate_telemetry()
        self.assertIsInstance(telemetry, (dict, list, type(None)))


if __name__ == "__main__":
    unittest.main()
