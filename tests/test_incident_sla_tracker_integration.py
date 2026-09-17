import unittest
import uuid
import random
from datetime import datetime, timedelta
from skills.incident_sla_tracker import IncidentSLATracker
from skills.incident_notification_bridge import IncidentNotificationBridge
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine

class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.thresholds = {"CRITICAL": 60, "HIGH": 300}
        self.tracker = IncidentSLATracker(self.thresholds, 0.8)
        self.notification_bridge = IncidentNotificationBridge()
        self.escalation_engine = IncidentAutoEscalationEngine()

    def test_sla_breach_flow_integration(self):
        incident_id = str(uuid.uuid4())
        severity = random.choice(["CRITICAL", "HIGH"])
        created_at = datetime.now() - timedelta(seconds=400)
        
        self.tracker.register_incident(incident_id, severity, created_at)
        
        # Проверка, что трекер корректно взаимодействует с реальными объектами
        # без использования моков, проверяя состояние системы
        results = self.tracker.check_sla_breaches(
            current_time=datetime.now(),
            notification_bridge=self.notification_bridge,
            escalation_engine=self.escalation_engine
        )
        
        # Проверяем, что инцидент попал в отчет о нарушениях
        found = any(r["incident_id"] == incident_id for r in results)
        self.assertTrue(found, f"Incident {incident_id} should have been flagged as breached")
        
        # Проверяем статус в трекере
        time_to_breach = self.tracker.get_time_to_breach(incident_id)
        self.assertLess(time_to_breach, 0, "Time to breach should be negative for a breached incident")

    def test_status_update_lifecycle(self):
        incident_id = str(uuid.uuid4())
        self.tracker.register_incident(incident_id, "CRITICAL", datetime.now())
        
        # Перевод в статус RESOLVED должен исключать инцидент из проверок SLA
        self.tracker.update_incident_status(incident_id, "RESOLVED")
        
        results = self.tracker.check_sla_breaches(
            current_time=datetime.now() + timedelta(seconds=200),
            notification_bridge=self.notification_bridge,
            escalation_engine=self.escalation_engine
        )
        
        # Инцидент не должен присутствовать в результатах, так как он RESOLVED
        for result in results:
            self.assertNotEqual(result["incident_id"], incident_id, "Resolved incident should not trigger breach")

if __name__ == '__main__':
    unittest.main()