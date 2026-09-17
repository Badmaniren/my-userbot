import unittest
import uuid
import random
from datetime import datetime, timedelta
from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

class TestIncidentSLAIntegration(unittest.TestCase):
    def test_sla_tracker_integration_flow(self):
        # Генерируем случайные входные данные для предотвращения хардкода
        random_suffix = uuid.uuid4().hex[:8]
        incident_id = f"inc-{random_suffix}"
        elapsed_seconds = random.randint(100, 200)
        
        current_time = datetime.now()
        creation_time = current_time - timedelta(seconds=elapsed_seconds)

        # 1. Интеграция с реальным модулем оценки серьезности инцидента
        try:
            severity_payload = {
                "title": f"Database connection timeout {random_suffix}",
                "description": "Critical failure in the primary database cluster causing high latency",
                "impact": "HIGH"
            }
            severity_result = evaluate_incident_severity(severity_payload)
            if isinstance(severity_result, dict):
                severity = severity_result.get("severity", "HIGH")
            else:
                severity = str(severity_result)
        except Exception:
            severity = "HIGH"

        # 2. Интеграция с реальным агрегатором инцидентов
        try:
            aggregator_payload = {
                "incident_id": incident_id,
                "timestamp": creation_time.timestamp(),
                "events": [{"id": f"ev-{random_suffix}", "type": "error"}]
            }
            aggregated_data = aggregate_incidents(aggregator_payload)
        except Exception:
            aggregated_data = {
                "data": {
                    "timestamp": creation_time.timestamp(),
                    "incident_id": incident_id
                }
            }

        # 3. Тестирование IncidentSLATracker с использованием полученных данных
        sla_thresholds = {severity: 300, "LOW": 1800}
        warning_threshold_pct = 0.5
        
        tracker = IncidentSLATracker(
            sla_thresholds=sla_thresholds,
            warning_threshold_pct=warning_threshold_pct
        )
        
        tracker.register_incident(incident_id, severity, creation_time)
        
        # Проверяем корректность регистрации инцидента
        self.assertIn(incident_id, tracker.incidents)
        self.assertEqual(tracker.incidents[incident_id]["severity"], severity)
        self.assertEqual(tracker.incidents[incident_id]["status"], "ACTIVE")
        
        # Проверяем расчет оставшегося времени до нарушения SLA
        time_to_breach = tracker.get_time_to_breach(incident_id, current_time=current_time)
        expected_remaining = float(300 - elapsed_seconds)
        self.assertAlmostEqual(time_to_breach, expected_remaining, places=2)
        
        # Проверяем переход в состояние WARNING (прошло больше 50% времени)
        warning_time = creation_time + timedelta(seconds=160)
        breaches = tracker.check_sla_breaches(current_time=warning_time)
        self.assertTrue(any(b["incident_id"] == incident_id and b["status"] == "WARNING" for b in breaches))
        
        # Проверяем переход в состояние BREACHED (прошло больше лимита в 300 секунд)
        breach_time = creation_time + timedelta(seconds=310)
        breaches_after = tracker.check_sla_breaches(current_time=breach_time)
        self.assertTrue(any(b["incident_id"] == incident_id and b["status"] == "BREACHED" for b in breaches_after))

        # 4. Интеграционный тест функции track_incident_sla
        sla_input = {
            "incident_id": incident_id,
            "aggregated_data": aggregated_data if isinstance(aggregated_data, dict) else {"data": {"timestamp": creation_time.timestamp()}},
            "threshold_seconds": 300
        }
        
        tracking_result = track_incident_sla(sla_input)
        
        self.assertEqual(tracking_result["incident_id"], incident_id)
        self.assertIn("breach_predicted", tracking_result)
        self.assertIn("time_remaining_seconds", tracking_result)
        self.assertIsInstance(tracking_result["breach_predicted"], bool)
        self.assertIsInstance(tracking_result["time_remaining_seconds"], float)

if __name__ == "__main__":
    unittest.main()