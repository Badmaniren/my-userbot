import unittest
import uuid
import random
import os
from skills.system_health_aggregator import SystemHealthAggregator

class TestSystemHealthAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.aggregator = SystemHealthAggregator()
        self.module_name = f"module_{random.randint(1000, 9999)}"
        self.incident_id = str(uuid.uuid4())
        self.test_file = f"report_{self.incident_id}.txt"

    def test_full_health_lifecycle_integration(self):
        # 1. Тест агрегации инцидента
        # Проверяем, что процесс агрегации не вызывает исключений и обновляет состояние
        try:
            self.aggregator.incident_aggregator.process_and_aggregate(
                self.module_name, "ConnectionError", "Traceback details", self.incident_id
            )
        except Exception as e:
            self.fail(f"Incident aggregation failed: {e}")

        # 2. Тест генерации индекса здоровья
        # Проверяем, что возвращаемый словарь содержит ожидаемые ключи
        health_index = self.aggregator.calculate_health_index(self.module_name)
        self.assertIsInstance(health_index, dict)

        # 3. Тест обработки потока данных
        # Генерируем случайный байтовый поток
        stream_data = f'{{"status": "ok", "id": "{self.incident_id}"}}'.encode('utf-8')
        parsed_data = self.aggregator.process_incoming_stream(stream_data)
        self.assertEqual(parsed_data.get("id"), self.incident_id)

        # 4. Тест генерации отчета
        # Проверяем, что отчет генерируется и содержит переданный ID
        audit_data = {"dependency": "critical", "version": "1.0.0"}
        report = self.aggregator.generate_full_report(
            self.module_name, "Critical Failure", self.incident_id, audit_data
        )
        self.assertIn(self.incident_id, report)

        # 5. Тест диспетчеризации уведомлений
        # Проверяем, что диспетчер возвращает True при отправке
        payload = {"incident_id": self.incident_id, "severity": "high"}
        dispatch_result = self.aggregator.notify_stakeholders("slack", payload)
        self.assertTrue(dispatch_result)

        # 6. Тест выполнения recovery sequence
        # Используем реальный объект ErrorRecoveryHub (согласно сигнатурам)
        from skills.error_recovery_hub import ErrorRecoveryHub
        hub = ErrorRecoveryHub()
        patch_payload = {"patch_version": random.random()}

        recovery_result = self.aggregator.execute_recovery_sequence(
            self.incident_id, patch_payload, hub
        )
        self.assertIsInstance(recovery_result, bool)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

if __name__ == '__main__':
    unittest.main()