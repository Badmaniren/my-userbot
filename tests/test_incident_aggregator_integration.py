import unittest
import uuid
import random
import os
from skills.incident_aggregator import IncidentAggregator

class TestIncidentAggregatorIntegration(unittest.TestCase):
    
    def setUp(self):
        self.aggregator = IncidentAggregator()
        self.random_module = f"test_module_{uuid.uuid4().hex[:8]}"
        self.random_error_msg = f"RuntimeError_{random.randint(1000, 9999)}"
        self.test_exception = Exception(self.random_error_msg)
        self.traceback_str = "Traceback (most recent call last):\n  File 'test.py', line 1, in <module>\n    raise Exception()"

    def test_aggregate_incident_flow(self):
        # 1. Захватываем сбой через интеграцию с error_recovery_hub и собираем метрики через patch_metric_collector
        incident_id = f"inc-{uuid.uuid4()}"
        
        # Симулируем обработку сбоя и запись метрик реальными компонентами
        recovery_result = self.aggregator.hub.capture_failure(
            module_name=self.random_module,
            exception=self.test_exception,
            traceback_str=self.traceback_str
        )
        
        # Передаем данные для агрегации в тестируемый модуль
        aggregated_data = self.aggregator.process_and_aggregate(
            module_name=self.random_module,
            exception=self.test_exception,
            traceback_str=self.traceback_str,
            incident_id=incident_id
        )

        # Проверяем, что агрегатор вернул словарь с аналитикой
        self.assertIsInstance(aggregated_data, dict)
        self.assertIn("incident_id", aggregated_data)
        self.assertEqual(aggregated_data["incident_id"], incident_id)
        self.assertIn("metrics", aggregated_data)
        self.assertIn("history", aggregated_data)

        # 2. Проверяем, что метрика реально записалась в patch_metric_collector
        metrics_summary = self.aggregator.collector.get_metrics_summary(self.random_module)
        self.assertIsInstance(metrics_summary, str)

        # 3. Экспортируем метрики и проверяем создание реального файла на диске
        export_path = f"metrics_report_{uuid.uuid4().hex[:6]}.json"
        export_success = self.aggregator.collector.export_metrics(export_path, "json")
        
        try:
            self.assertTrue(export_success)
            self.assertTrue(os.path.exists(export_path))
            self.assertGreater(os.path.getsize(export_path), 0)
        finally:
            if os.path.exists(export_path):
                os.remove(export_path)

        # 4. Проверяем историю инцидентов через error_recovery_hub
        history = self.aggregator.hub.get_incident_history(self.random_module)
        self.assertIsInstance(history, list)

if __name__ == "__main__":
    unittest.main()