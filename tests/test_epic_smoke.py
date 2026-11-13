import unittest
import json
import tempfile
import os
from pathlib import Path
from repo_health_incident_tracker import IncidentTracker, Incident, EscalationPolicy

class TestIncidentTrackerRealConditions(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.test_dir.name) / "incidents_audit.json"
        
        # Создаем реалистичные данные инцидентов здоровья репозитория (20-30 строк логов/событий)
        self.raw_events = [
            {"id": "INC-1001", "severity": "LOW", "component": "dependency_scanner", "message": "Outdated minor version detected in requirements.txt", "timestamp": "2023-10-25T08:30:00Z"},
            {"id": "INC-1002", "severity": "MEDIUM", "component": "repo_auditor", "message": "Unused configuration file found in root directory", "timestamp": "2023-10-25T09:15:00Z"},
            {"id": "INC-1003", "severity": "HIGH", "component": "vulnerability_analyzer", "message": "Critical CVE found in transitive dependency numpy@1.16.0", "timestamp": "2023-10-25T10:00:00Z"},
            {"id": "INC-1004", "severity": "CRITICAL", "component": "repo_ci_pipeline", "message": "Main branch build pipeline failed on security gate check", "timestamp": "2023-10-25T10:05:00Z"},
            {"id": "INC-1005", "severity": "LOW", "component": "changelog_generator", "message": "Missing commit message convention in recent PR", "timestamp": "2023-10-25T11:20:00Z"},
            {"id": "INC-1006", "severity": "HIGH", "component": "repo_security_gateway", "message": "Unauthorized access attempt blocked on release branch", "timestamp": "2023-10-25T12:00:00Z"},
            {"id": "INC-1007", "severity": "MEDIUM", "component": "repo_backup", "message": "Incremental backup completed with 2 warnings", "timestamp": "2023-10-25T13:45:00Z"},
            {"id": "INC-1008", "severity": "CRITICAL", "component": "repo_health_guardian", "message": "Repository memory limit exceeded during telemetry aggregation", "timestamp": "2023-10-25T14:10:00Z"},
            {"id": "INC-1009", "severity": "LOW", "component": "repo_tagger", "message": "Tag format non-compliant with SemVer schema", "timestamp": "2023-10-25T15:00:00Z"},
            {"id": "INC-1010", "severity": "MEDIUM", "component": "dependency_updater_pipeline", "message": "Automatic PR merge conflict detected", "timestamp": "2023-10-25T15:30:00Z"}
        ]
        
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(self.raw_events, f, indent=2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_incident_processing_and_escalation(self):
        print("\n[PRAXIS CHECK] Инициализация IncidentTracker с реальными данными с диска...")
        
        policy = EscalationPolicy(
            critical_threshold_minutes=15,
            high_threshold_minutes=30,
            default_channels=["console", "webhook"]
        )
        
        tracker = IncidentTracker(storage_path=self.log_path, escalation_policy=policy)
        loaded_incidents = tracker.load_incidents()
        
        print(f"[PRAXIS CHECK] Успешно загружено инцидентов из файла: {len(loaded_incidents)}")
        self.assertEqual(len(loaded_incidents), 10)

        # Обработка и эскалация
        escalated_count = 0
        processed_results = []

        for inc_data in loaded_incidents:
            incident = Incident(**inc_data)
            action = tracker.evaluate_and_escalate(incident)
            processed_results.append({
                "id": incident.id,
                "severity": incident.severity,
                "action_taken": action
            })
            if action.get("escalated"):
                escalated_count += 1

        print("\r\n--- РЕЗУЛЬТАТЫ АВТОМАТИЧЕСКОГО ОПОВЕЩЕНИЯ И ЭСКАЛАЦИИ ---")
        for res in processed_results:
            print(f"Инцидент {res['id']} [{res['severity']}]: Действие -> {res['action_taken']}")
        print(f"----------------------------------------------------------")
        print(f"[PRAXIS CHECK] Всего эскалировано критических/высоких инцидентов: {escalated_count}")

        # Проверяем, что критические и высокие инциденты были успешно эскалированы согласно политике
        self.assertGreaterEqual(escalated_count, 4, "Критические и высокие инциденты должны быть эскалированы")

        # Проверка генерации отчета об эскалации
        report = tracker.generate_escalation_report()
        print(f"[PRAXIS CHECK] Сгенерирован отчет об эскалации. Статус трекера: {report.get('status')}")
        self.assertEqual(report.get("total_processed"), 10)
        self.assertIn("escalation_summary", report)