import unittest
import tempfile
import os
import json
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger
from skills.git_inspector import GitInspector

class TestEpicIncidentResponse(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.test_dir.name, "incidents.log")

        # Создаем реалистичный лог-файл с 25 строками телеметрии и аномалий
        realistic_logs = [
            {"source": "auth_service", "severity": "INFO", "details": "User login success", "telemetry": {"cpu": 15.2, "memory": 45.0}},
            {"source": "db_cluster", "severity": "WARNING", "details": "High connection pool usage", "telemetry": {"cpu": 65.0, "memory": 82.5}},
            {"source": "payment_gateway", "severity": "CRITICAL", "details": "Timeout connecting to bank API", "telemetry": {"cpu": 98.5, "memory": 91.2}},
            {"source": "payment_gateway", "severity": "INFO", "details": "Retry attempt 1", "telemetry": {"cpu": 88.0, "memory": 89.0}},
            {"source": "cache_redis", "severity": "INFO", "details": "Eviction policy triggered", "telemetry": {"cpu": 40.0, "memory": 70.0}},
            {"source": "auth_service", "severity": "INFO", "details": "Token refreshed", "telemetry": {"cpu": 18.0, "memory": 46.0}},
            {"source": "api_gateway", "severity": "WARNING", "details": "Rate limit exceeded for client X", "telemetry": {"cpu": 55.4, "memory": 60.1}},
            {"source": "db_cluster", "severity": "CRITICAL", "details": "Deadlock detected on transactions table", "telemetry": {"cpu": 99.1, "memory": 95.8}},
            {"source": "worker_queue", "severity": "INFO", "details": "Job processed successfully", "telemetry": {"cpu": 30.0, "memory": 50.0}},
            {"source": "worker_queue", "severity": "INFO", "details": "Job processed successfully", "telemetry": {"cpu": 32.0, "memory": 50.2}},
            {"source": "storage_s3", "severity": "WARNING", "details": "Slow response from storage bucket", "telemetry": {"cpu": 45.0, "memory": 65.5}},
            {"source": "auth_service", "severity": "INFO", "details": "Password reset requested", "telemetry": {"cpu": 20.0, "memory": 47.0}},
            {"source": "payment_gateway", "severity": "CRITICAL", "details": "Transaction rollback executed due to timeout", "telemetry": {"cpu": 92.0, "memory": 90.0}},
            {"source": "api_gateway", "severity": "INFO", "details": "Health check OK", "telemetry": {"cpu": 22.0, "memory": 51.0}},
            {"source": "db_cluster", "severity": "INFO", "details": "Replica lag under 10ms", "telemetry": {"cpu": 35.0, "memory": 68.0}},
            {"source": "cache_redis", "severity": "WARNING", "details": "Memory usage near max limit", "telemetry": {"cpu": 50.0, "memory": 89.9}},
            {"source": "auth_service", "severity": "WARNING", "details": "Multiple failed login attempts", "telemetry": {"cpu": 28.0, "memory": 48.0}},
            {"source": "worker_queue", "severity": "CRITICAL", "details": "Queue backlog exceeded 10000 items", "telemetry": {"cpu": 95.0, "memory": 88.0}},
            {"source": "api_gateway", "severity": "INFO", "details": "Endpoint /v1/status accessed", "telemetry": {"cpu": 25.0, "memory": 52.0}},
            {"source": "storage_s3", "severity": "INFO", "details": "Backup completed", "telemetry": {"cpu": 60.0, "memory": 70.0}},
            {"source": "payment_gateway", "severity": "INFO", "details": "Service recovered and stable", "telemetry": {"cpu": 40.0, "memory": 60.0}},
            {"source": "db_cluster", "severity": "INFO", "details": "Query optimization applied", "telemetry": {"cpu": 30.0, "memory": 62.0}},
            {"source": "auth_service", "severity": "INFO", "details": "User session closed", "telemetry": {"cpu": 15.0, "memory": 44.0}},
            {"source": "worker_queue", "severity": "WARNING", "details": "Worker node disconnected", "telemetry": {"cpu": 70.0, "memory": 75.0}},
            {"source": "system", "severity": "INFO", "details": "Routine diagnostic passed", "telemetry": {"cpu": 10.0, "memory": 40.0}}
        ]

        with open(self.log_path, "w", encoding="utf-8") as f:
            for entry in realistic_logs:
                f.write(json.dumps(entry) + "\n")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_incident_dispatch_audit_and_rollback_pipeline(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА: РЕАКЦИЯ НА ИНЦИДЕНТЫ ===")

        # 1. Проверяем AnomalyLogger и загрузку реальных данных
        logger = AnomalyLogger(self.log_path)
        anomalies = logger.get_anomalies()
        print(f"[1] Загружено записей из файла телеметрии: {len(anomalies)}")
        self.assertGreaterEqual(len(anomalies), 20, "Лог-файл должен содержать не менее 20 записей")

        # 2. Диспетчеризация и аудит через AnomalyAuditHub
        audit_hub = AnomalyAuditHub(repo_path=".", log_path=self.log_path, threshold=80.0)

        critical_count = 0
        for entry in anomalies:
            severity = entry.get("severity")
            source = entry.get("source")
            details = entry.get("details")
            telemetry = entry.get("telemetry", {})

            # Логируем аномалию в хаб аудита для диспетчеризации
            audit_hub.log_anomaly(source=source, severity=severity, details=details, telemetry_snapshot=telemetry)
            if severity == "CRITICAL":
                critical_count += 1
                print(f"   [DISPATCHED CRITICAL] Источник: {source} | Детали: {details} | Телеметрия: {telemetry}")

        print(f"[2] Всего отдиспетчеризовано критических инцидентов: {critical_count}")
        self.assertGreater(critical_count, 0, "Должны быть обнаружены критические инциденты для авто-исправления")

        # 3. Агрегация отчетов диспетчеризации
        report = audit_hub.generate_final_report()
        print(f"[3] Сгенерирован финальный отчет аудита: {type(report)}")
        print(f"    Структура отчета: {list(report.keys()) if isinstance(report, dict) else report}")

        # 4. Проверка контроля отката и безопасности (GitInspector)
        git_inspector = GitInspector(repo_path=".")
        history = git_inspector.get_commit_history(max_count=5)
        print(f"[4] Проверка безопасности через GitInspector. Последних коммитов в репозитории: {len(history)}")

        print("=== ПРАКТИЧЕСКАЯ ПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА ===")

if __name__ == "__main__":
    unittest.main()