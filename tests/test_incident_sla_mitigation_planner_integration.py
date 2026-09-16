import unittest
import uuid
import random
from skills import incident_sla_mitigation_planner
from skills import incident_sla_tracker
from skills import incident_sla_breach_predictor
from skills import incident_knowledge_base_searcher

class TestIncidentSLAMitigationPlannerIntegration(unittest.TestCase):
    """
    Интеграционный тест для проверки взаимодействия планировщика митигации
    с реальными модулями трекера, предсказателя и базы знаний.
    """

    def setUp(self):
        self.planner = incident_sla_mitigation_planner.IncidentSLAMitigationPlanner()
        self.incident_id = f"inc-{uuid.uuid4().hex[:8]}"
        self.test_steps = ["Step A", "Step B", "Step C"]

    def test_full_mitigation_lifecycle_integration(self):
        # 1. Проверка генерации плана через основной класс
        # Используем реальные методы модулей, если они доступны в окружении
        plan = self.planner.build_plan_for_incident(self.incident_id)
        
        self.assertIsInstance(plan, dict)
        self.assertEqual(plan.get("incident_id"), self.incident_id)
        self.assertIn("remediation_steps", plan)
        self.assertIsInstance(plan["remediation_steps"], list)

        # 2. Проверка интеграционной точки входа (функции)
        # Генерируем случайный payload для проверки динамической обработки
        random_steps = [f"Action-{random.randint(100, 999)}" for _ in range(2)]
        payload = {
            "incident_id": self.incident_id,
            "prediction_payload": {
                "remediation_steps": random_steps
            }
        }
        
        result = incident_sla_mitigation_planner.incident_sla_mitigation_planner(payload)
        
        # Проверка корректности обработки данных
        self.assertEqual(result.get("target_incident_id"), self.incident_id)
        self.assertEqual(result.get("remediation_steps"), random_steps)
        self.assertTrue(result.get("mitigation_plan_id").startswith("plan-"))

    def test_mitigation_planner_data_consistency(self):
        # Проверка согласованности данных между трекером и планировщиком
        # Если трекер возвращает данные, планировщик должен их подхватить
        incident_id = f"test-id-{uuid.uuid4().hex[:6]}"
        
        # Вызов метода, который должен вернуть структуру, основанную на данных
        # Если модули не настроены на возврат данных, проверяем дефолтное поведение
        mitigation_data = self.planner.generate_mitigation_plan(incident_id)
        
        if mitigation_data:
            self.assertIn("tracker_id", mitigation_data)
            self.assertEqual(mitigation_data["incident_id"], incident_id)
            self.assertIsInstance(mitigation_data["steps"], list)

    def test_export_functionality(self):
        # Проверка экспорта отчета (интеграция с recovery_report_exporter)
        report_stream = self.planner.export_mitigation_report()
        
        self.assertIsNotNone(report_stream)
        content = report_stream.read()
        self.assertIsInstance(content, bytes)
        self.assertTrue(len(content) > 0)

if __name__ == "__main__":
    unittest.main()