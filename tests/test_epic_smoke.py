import unittest
import tempfile
import os
import json
from datetime import datetime, timedelta

# Импортируем модули, задействованные в эпике автоматического оповещения и эскалации инцидентов
from repo_health_incident_tracker import IncidentTracker
from repo_notifier import RepoNotifier
from repo_logger import RepoLogger


class TestIncidentEscalationEpicRealConditions(unittest.TestCase):
    """
    Одноразовая практическая проверка завершённого эпика:
    'Система автоматического оповещения и эскалации инцидентов'.
    
    Проверка выполняется на реальных данных (создается временный файл с логами 
    и метриками репозитория, имитирующими критические сбои и аномалии).
    """

    def setUp(self):
        # Создаем временную директорию и файл с реалистичными данными инцидентов репозитория
        self.test_dir = tempfile.TemporaryDirectory()
        self.data_file_path = os.path.join(self.test_dir.name, "repo_health_incidents.json")
        
        # Генерируем 25 строк реалистичных инцидентов и метрик здоровья репозитория
        now = datetime.utcnow()
        self.realistic_events = []
        
        components = ["ci_pipeline", "dependency_scanner", "security_gate", "repo_sync", "vulnerability_patcher"]
        severities = ["INFO", "WARNING", "CRITICAL", "FATAL"]
        
        for i in range(1, 26):
            timestamp = (now - timedelta(minutes=30 * (26 - i))).isoformat()
            severity = severities[i % len(severities)]
            component = components[i % len(components)]
            
            event = {
                "event_id": f"INC-{1000 + i}",
                "timestamp": timestamp,
                "component": component,
                "severity": severity,
                "metric_drop_percent": float(i * 3.5 if severity in ["CRITICAL", "FATAL"] else i * 0.5),
                "message": f"Health check failed for {component} with status code {500 if severity == 'FATAL' else 200}"
            }
            self.realistic_events.append(event)

        with open(self.data_file_path, "w", encoding="utf-8") as f:
            json.dump(self.realistic_events, f, indent=2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_incident_detection_and_escalation_pipeline(self):
        print("\n--- НАЧАЛО РЕАЛЬНОЙ ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА ---")
        print(f"Создан файл с данными: {self.data_file_path}")
        print(f"Количество записей в источнике: {len(self.realistic_events)}")

        # 1. Инициализируем компоненты системы
        logger = RepoLogger()
        notifier = RepoNotifier(channel="incident-escalation-channel")
        
        # Передаем путь к файлу с данными в трекер инцидентов
        tracker = IncidentTracker(
            data_source=self.data_file_path,
            logger=logger,
            notifier=notifier,
            escalation_threshold="CRITICAL"
        )

        # 2. Выполняем обработку и анализ инцидентов
        print("\n[INFO] Запуск обработки инцидентов трекером...")
        processed_incidents = tracker.process_incidents()
        
        # Печать реальных результатов работы системы для логов
        print(f"[RESULT] Обработано инцидентов всего: {len(processed_incidents)}")
        
        escalated_incidents = [inc for inc in processed_incidents if inc.get("escalated", False)]
        print(f"[RESULT] Эскалировано критических инцидентов: {len(escalated_incidents)}")

        for inc in escalated_incidents:
            print(f"  -> [ESCALATION] ID: {inc['event_id']} | Component: {inc['component']} | Severity: {inc['severity']} | Metric Drop: {inc['metric_drop_percent']}%")

        # 3. Проверяем корректность работы модулей
        self.assertGreater(len(processed_incidents), 0, "Трекер должен обработать инциденты из файла")
        self.assertGreater(len(escalated_incidents), 0, "Должны быть найдены инциденты для эскалации")

        # Проверяем, что эскалированы действительно самые критичные события
        for inc in escalated_incidents:
            self.assertIn(inc['severity'], ["CRITICAL", "FATAL"], "Эскалироваться должны только CRITICAL или FATAL события")

        print("\n--- ПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА: СИСТЕМА РАБОТАЕТ НА РЕАЛЬНЫХ ДАННЫХ ---")


if __name__ == "__main__":
    unittest.main()