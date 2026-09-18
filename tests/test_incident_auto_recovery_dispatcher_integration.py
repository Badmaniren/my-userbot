import unittest
import uuid
import random
import os
from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine
from skills.error_recovery_hub import ErrorRecoveryHub

class TestIncidentAutoRecoveryDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.dispatcher = IncidentAutoRecoveryDispatcher()
        self.incident_id = str(uuid.uuid4())
        self.module_name = f"test_module_{random.randint(1000, 9999)}"
        self.exception = RuntimeError("Integration test failure")
        self.traceback = "Traceback (most recent call last): File 'test.py', line 1, in <module>"

    def test_full_recovery_cycle_integration(self):
        """
        Проверка реального взаимодействия между Dispatcher, RecoveryHub и EscalationEngine.
        Проверяем, что цепочка вызовов проходит без ошибок и возвращает логические результаты.
        """
        result = self.dispatcher.run_full_recovery_cycle(
            self.module_name, 
            self.exception, 
            self.traceback
        )
        
        # Проверяем, что результат является булевым значением (успех/провал цикла)
        self.assertIsInstance(result, bool)

    def test_dispatch_recovery_flow(self):
        """
        Проверка интеграции данных между компонентами при диспетчеризации восстановления.
        """
        response = self.dispatcher.dispatch_recovery(
            self.incident_id, 
            self.module_name, 
            self.exception
        )
        
        # Проверка структуры ответа
        self.assertIn("incident_id", response)
        self.assertEqual(response["incident_id"], self.incident_id)
        self.assertEqual(response["status"], "dispatched")
        
        # Проверка, что компоненты реально отработали и вернули данные
        self.assertIsNotNone(response["recovery_result"])
        self.assertIsNotNone(response["escalation_result"])

    def test_telemetry_and_stream_consistency(self):
        """
        Проверка того, что методы делегирования к EscalationEngine возвращают корректные типы данных.
        """
        telemetry = self.dispatcher.evaluate_telemetry()
        self.assertIsInstance(telemetry, dict)
        
        stream_data = self.dispatcher.consume_and_process_stream()
        self.assertIsInstance(stream_data, bytes)

    def test_no_circular_dependency_on_init(self):
        """
        Проверка корректности инициализации без возникновения циклических импортов.
        """
        try:
            dispatcher = IncidentAutoRecoveryDispatcher()
            self.assertIsInstance(dispatcher.escalation_engine, IncidentAutoEscalationEngine)
            self.assertIsInstance(dispatcher.recovery_hub, ErrorRecoveryHub)
        except ImportError as e:
            self.fail(f"Инициализация вызвала ошибку импорта: {e}")

if __name__ == '__main__':
    unittest.main()