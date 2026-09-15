import unittest
import uuid
import random
import os
from skills.incident_severity_evaluator import IncidentSeverityEvaluator
from skills.incident_aggregator import IncidentAggregator
from skills.notification_template_engine import NotificationTemplateEngine

class TestIncidentSeverityEvaluatorIntegration(unittest.TestCase):
    def setUp(self):
        self.evaluator = IncidentSeverityEvaluator()
        self.aggregator = IncidentAggregator()
        self.engine = NotificationTemplateEngine()
        self.incident_id = str(uuid.uuid4())
        self.module_name = f"test_module_{random.randint(1000, 9999)}"
        self.exception_msg = f"RuntimeError: Critical failure {random.randint(1, 100)}"
        self.traceback_str = f"Traceback (most recent call last):\n  File '{self.module_name}.py', line {random.randint(1, 50)}, in <module>\n    raise RuntimeError()"

    def test_composite_incident_evaluation_flow(self):
        # Шаг 1: Проверяем реальную работу агрегатора в составе композитного модуля
        aggregated_data = self.aggregator.process_and_aggregate(
            module_name=self.module_name,
            exception=Exception(self.exception_msg),
            traceback_str=self.traceback_str,
            incident_id=self.incident_id
        )
        
        self.assertIsInstance(aggregated_data, dict)
        self.assertIn("incident_id", aggregated_data)
        self.assertEqual(aggregated_data["incident_id"], self.incident_id)

        # Шаг 2: Проверяем работу движка шаблонов через оценщик критичности
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        payload = self.engine.generate_notification_payload(
            severity=severity_level,
            incident_id=self.incident_id,
            raw_data=aggregated_data
        )
        
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload.get("severity"), severity_level)

        # Шаг 3: Проверяем полный интеграционный метод модуля оценки критичности без моков
        eval_result = self.evaluator.evaluate_and_notify(
            module_name=self.module_name,
            exception=Exception(self.exception_msg),
            traceback_str=self.traceback_str,
            incident_id=self.incident_id
        )

        self.assertIsInstance(eval_result, dict)
        self.assertEqual(eval_result.get("incident_id"), self.incident_id)
        self.assertIn("severity", eval_result)
        self.assertIn("notification", eval_result)

        # Шаг 4: Проверяем реальный экспорт артефакта уведомления файловой системы
        export_path = f"incident_report_{self.incident_id}.txt"
        export_success = self.engine.export_notification_file(
            context=eval_result,
            file_path=export_path
        )
        
        try:
            self.assertTrue(export_success)
            self.assertTrue(os.path.exists(export_path))
            with open(export_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(self.incident_id, content)
        finally:
            if os.path.exists(export_path):
                os.remove(export_path)

if __name__ == "__main__":
    unittest.main()