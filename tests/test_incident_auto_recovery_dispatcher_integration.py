import unittest
import uuid
import random
import os
from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher
from skills.incident_sla_recovery_coordinator import IncidentSlaRecoveryCoordinator

class TestIncidentAutoRecoveryDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()
        self.sla_coordinator = IncidentSlaRecoveryCoordinator()
        self.incident_id = str(uuid.uuid4())
        self.module_name = f"module_{random.randint(1000, 9999)}"
        self.exception = RuntimeError(f"Critical failure in {self.module_name}")
        self.traceback = "Traceback (most recent call last): File 'main.py', line 1"

    def test_full_recovery_cycle_integration(self):
        """
        Интеграционный тест: проверяет связку диспетчера восстановления
        и SLA-координатора без использования моков.
        """
        # 1. Запуск цикла восстановления
        recovery_success = self.dispatcher.run_full_recovery_cycle(
            self.module_name, 
            self.exception, 
            self.traceback
        )
        
        # 2. Проверка, что диспетчер вернул булево значение (результат деплоя)
        self.assertIsInstance(recovery_success, bool)

        # 3. Проверка интеграции с SLA-координатором
        # Если восстановление прошло, SLA-координатор должен зафиксировать статус
        sla_status = self.sla_coordinator.get_recovery_status(self.incident_id)

        # Если диспетчер отработал, в системе должен существовать след инцидента
        # Проверяем, что координатор видит состояние инцидента
        self.assertIsNotNone(sla_status)

        # 4. Проверка диспетчеризации
        dispatch_result = self.dispatcher.dispatch_recovery(
            self.incident_id, 
            self.module_name, 
            self.exception
        )
        
        self.assertEqual(dispatch_result["incident_id"], self.incident_id)
        self.assertEqual(dispatch_result["status"], "dispatched")
        self.assertIn("recovery_result", dispatch_result)
        self.assertIn("escalation_result", dispatch_result)

    def test_telemetry_and_stream_consistency(self):
        """
        Проверка консистентности данных при обработке потока телеметрии.
        """
        telemetry_data = self.dispatcher.evaluate_telemetry()
        self.assertIsInstance(telemetry_data, dict)
        
        stream_data = self.dispatcher.consume_and_process_stream()
        self.assertIsInstance(stream_data, bytes)
        self.assertGreater(len(stream_data), 0)

if __name__ == '__main__':
    unittest.main()