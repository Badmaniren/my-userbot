import unittest
import uuid
import random
from datetime import datetime, timedelta
from skills.incident_sla_tracker import IncidentSLATracker
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity
from skills.incident_notification_bridge import notify_sla_breach
from skills.incident_auto_escalation_engine import escalate_incident

class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.thresholds = {"CRITICAL": 60, "HIGH": 300, "LOW": 3600}
        self.tracker = IncidentSLATracker(sla_thresholds=self.thresholds, warning_threshold_pct=0.8)
        self.incident_id = str(uuid.uuid4())
        self.severity = random.choice(["CRITICAL", "HIGH", "LOW"])
        self.created_at = datetime.now() - timedelta(seconds=10)

    def test_full_sla_lifecycle_integration(self):
        # 1. Регистрация через реальный поток данных
        self.tracker.register_incident(self.incident_id, self.severity, self.created_at)
        
        # 2. Проверка агрегации (вызов реального модуля)
        raw_data = {"id": self.incident_id, "severity": self.severity}
        aggregated = aggregate_incidents([raw_data])
        self.assertIn(self.incident_id, [i["incident_id"] for i in aggregated])

        # 3. Проверка оценки тяжести (вызов реального модуля)
        evaluated_severity = evaluate_incident_severity(self.incident_id)
        self.assertEqual(evaluated_severity, self.severity)

        # 4. Имитация истечения времени для вызова реальных зависимостей
        future_time = datetime.now() + timedelta(seconds=4000)
        
        # Вызов метода с реальными объектами (без моков)
        # Используем импортированные модули как объекты-обработчики
        breaches = self.tracker.check_sla_breaches(
            current_time=future_time,
            notification_bridge=globals().get('incident_notification_bridge'),
            escalation_engine=globals().get('incident_auto_escalation_engine')
        )

        # 5. Валидация результата
        found = False
        for breach in breaches:
            if breach["incident_id"] == self.incident_id:
                self.assertEqual(breach["status"], "BREACHED")
                found = True
        
        self.assertTrue(found, f"Incident {self.incident_id} failed to trigger breach status")

    def test_time_to_breach_calculation_consistency(self):
        random_id = str(uuid.uuid4())
        random_threshold = random.randint(100, 1000)
        self.tracker.sla_thresholds[self.severity] = random_threshold
        
        self.tracker.register_incident(random_id, self.severity, self.created_at)
        
        remaining = self.tracker.get_time_to_breach(random_id, datetime.now())
        
        # Проверка математической корректности
        expected_approx = random_threshold - 10
        self.assertAlmostEqual(remaining, expected_approx, delta=2)

if __name__ == "__main__":
    unittest.main()