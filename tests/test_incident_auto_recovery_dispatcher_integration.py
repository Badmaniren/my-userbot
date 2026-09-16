import unittest
import uuid
import random
from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher


class TestIncidentAutoRecoveryDispatcherIntegration(unittest.TestCase):
    """
    Интеграционный тест для IncidentAutoRecoveryDispatcher.
    Проверяет реальное взаимодействие без моков между 
    IncidentAutoEscalationEngine и ErrorRecoveryHub.
    """

    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()
        self.module_name = f"test_module_{uuid.uuid4().hex[:8]}"
        self.incident_id = f"inc-{uuid.uuid4().hex}"
        self.exception_msg = f"Random failure {uuid.uuid4().hex}"
        self.test_exception = RuntimeError(self.exception_msg)
        self.traceback_str = f"Traceback (most recent call last):\n  File '{self.module_name}.py', line {random.randint(1, 100)}\n    raise RuntimeError('{self.exception_msg}')"

    def test_dispatch_recovery_integration(self):
        # Проверяем сквозной метод dispatch_recovery с использованием реальных навыков
        result = self.dispatcher.dispatch_recovery(
            incident_id=self.incident_id,
            module_name=self.module_name,
            exception=self.test_exception
        )

        self.assertIsInstance(result, dict, "Результат должен быть словарем")
        self.assertEqual(result.get("incident_id"), self.incident_id, "Инцидент ID должен совпадать")
        self.assertEqual(result.get("status"), "dispatched", "Статус должен быть dispatched")
        
        # Проверяем, что вложенные результаты получены от реальных движков
        self.assertIn("recovery_result", result)
        self.assertIn("escalation_result", result)

    def test_evaluate_telemetry_integration(self):
        # Проверяем интеграцию с IncidentAutoEscalationEngine.evaluate_system_telemetry_risks
        telemetry = self.dispatcher.evaluate_telemetry()
        self.assertIsInstance(telemetry, dict, "Телеметрия должна возвращаться в виде словаря")

    def test_consume_and_process_stream_integration(self):
        # Проверяем интеграцию с IncidentAutoEscalationEngine.consume_stream_data
        stream_data = self.dispatcher.consume_and_process_stream()
        self.assertTrue(
            isinstance(stream_data, (bytes, bytearray)), 
            "Поток данных должен возвращаться в байтах"
        )

    def test_run_full_recovery_cycle_integration(self):
        # Проверяем полный цикл восстановления и эскалации
        success = self.dispatcher.run_full_recovery_cycle(
            module_name=self.module_name,
            exception=self.test_exception,
            traceback_str=self.traceback_str
        )
        self.assertIsInstance(success, bool, "Результат полного цикла должен быть булевым значением")


if __name__ == "__main__":
    unittest.main()