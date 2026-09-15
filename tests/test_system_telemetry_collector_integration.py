import unittest
import uuid
import random
import sys
import os

from skills.system_telemetry_collector import SystemTelemetryCollector
from skills.error_recovery_hub import ErrorRecoveryHub

class TestSystemTelemetryCollectorIntegration(unittest.TestCase):
    def setUp(self):
        self.hub = ErrorRecoveryHub()
        self.collector = SystemTelemetryCollector(error_recovery_hub=self.hub)
        self.random_module_name = f"test_module_{uuid.uuid4().hex[:8]}"
        self.random_error_msg = f"RuntimeError_{uuid.uuid4().hex[:6]}"

    def test_telemetry_and_error_recovery_integration(self):
        test_exception = RuntimeError(self.random_error_msg)
        random_cpu_load = round(random.uniform(10.0, 99.9), 2)

        try:
            raise test_exception
        except RuntimeError as e:
            tb = sys.exc_info()[2]
            incident_id = self.hub.capture_failure(
                module_name=self.random_module_name,
                exception=e,
                traceback_str=str(tb)
            )

        self.assertIsNotNone(incident_id, "Hub должен вернуть incident_id при фиксации сбоя")

        telemetry_payload = {
            "module": self.random_module_name,
            "incident_id": incident_id,
            "cpu_load": random_cpu_load,
            "memory_usage": random.randint(1024, 8192)
        }

        self.collector.collect_metrics(telemetry_payload)

        logs = self.hub.get_incident_logs(incident_id)
        history = self.hub.get_incident_history(self.random_module_name)

        self.assertTrue(any(incident_id in str(item) for item in history), "История инцидентов должна содержать созданный ID")
        self.assertIsNotNone(logs, "Логи инцидента не должны быть пустыми после сбора телеметрии")

if __name__ == "__main__":
    unittest.main()