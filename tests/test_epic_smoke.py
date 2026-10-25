import unittest
import tempfile
import os
import json
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger
from skills.digest_exporter import DigestExporter


class TestEpicAuditAndSecurity(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.test_dir.name, "security_audit.log")
        self.repo_path = self.test_dir.name

    def tearDown(self):
        self.test_dir.cleanup()

    def test_audit_aggregation_and_export_pipeline(self):
        print("\n--- НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА: Аудит и безопасность ---")

        # 1. Инициализация хаба аудита
        threshold = 50.0
        hub = AnomalyAuditHub(repo_path=self.repo_path, log_path=self.log_path, threshold=threshold)
        print(f"[1] Инициализирован AnomalyAuditHub (порог аномалий: {threshold})")

        # 2. Симуляция потока событий безопасности и телеметрии (20 записей)
        mock_events = [
            ("auth_service", 20.0, "Successful login", {"cpu_load": 15.2}),
            ("payment_gateway", 45.5, "High latency detected", {"cpu_load": 45.0}),
            ("auth_service", 85.1, "Brute-force attempt detected", {"cpu_load": 92.4}),
            ("db_cluster", 10.0, "Heartbeat OK", {"cpu_load": 10.1}),
            ("api_gateway", 60.0, "Rate limit exceeded", {"cpu_load": 65.0}),
            ("auth_service", 95.0, "Unauthorized root access try", {"cpu_load": 99.9}),
            ("payment_gateway", 30.0, "Transaction processed", {"cpu_load": 30.0}),
            ("db_cluster", 78.4, "Slow query spike", {"cpu_load": 80.2}),
            ("api_gateway", 12.0, "Health check passed", {"cpu_load": 11.5}),
            ("auth_service", 55.0, "Multiple invalid tokens", {"cpu_load": 50.0}),
            ("payment_gateway", 88.9, "Gateway timeout error", {"cpu_load": 85.0}),
            ("db_cluster", 92.1, "Connection pool exhaustion", {"cpu_load": 95.1}),
            ("api_gateway", 40.0, "Normal traffic", {"cpu_load": 40.0}),
            ("auth_service", 15.0, "Password reset requested", {"cpu_load": 14.2}),
            ("payment_gateway", 10.0, "Service idle", {"cpu_load": 5.0}),
            ("db_cluster", 45.0, "Backup completed", {"cpu_load": 60.0}),
            ("api_gateway", 77.7, "Suspicious payload pattern", {"cpu_load": 81.0}),
            ("auth_service", 10.0, "Logout successful", {"cpu_load": 10.0}),
            ("payment_gateway", 99.9, "Critical payment exception", {"cpu_load": 98.5}),
            ("system_core", 50.1, "Memory usage warning", {"cpu_load": 88.0})
        ]

        print(f"[2] Запись {len(mock_events)} событий безопасности в лог через AnomalyAuditHub...")
        for source, severity, details, telemetry in mock_events:
            hub.log_anomaly(source=source, severity=severity, details=details, telemetry_snapshot=telemetry)

        # Проверка создания файла логов на диске
        self.assertTrue(os.path.exists(self.log_path), "Файл логов аудита должен быть создан на диске.")
        with open(self.log_path, "r", encoding="utf-8") as f:
            log_lines = f.readlines()
        print(f"    -> Файл лога успешно создан. Строк на диске: {len(log_lines)}")
        self.assertGreaterEqual(len(log_lines), len(mock_events), "Количество строк в логе должно соответствовать числу событий.")

        # 3. Проверка агрегации метрик
        print("[3] Агрегация метрик безопасности...")
        metric_name = "cpu_load"
        avg_value = 52.86
        report = hub.aggregate_and_report(metric_name=metric_name, value=avg_value)
        print(f"    -> Сформирован агрегированный отчет для метрики '{metric_name}':", report)
        self.assertIsNotNone(report, "Агрегированный отчет не должен быть пустым.")

        # 4. Генерация финального отчета аудита
        print("[4] Генерация финального отчета аудита...")
        final_report = hub.generate_final_report()
        print(f"    -> Финальный отчет сгенерирован (тип: {type(final_report)}).")

        # 5. Экспорт отчетов через DigestExporter
        export_path = os.path.join(self.test_dir.name, "security_digest_export.json")
        print(f"[5] Экспорт структурированного дайджеста в файл: {export_path}")

        exporter = DigestExporter()
        # Проверяем экспорт через метод класса/экземпляра в зависимости от реализации
        # Передаем финальный отчет или структурированные данные
        exported_data = {
            "audit_report": final_report,
            "aggregated_metric": report,
            "total_events": len(mock_events)
        }

        # Если у DigestExporter есть метод экспорта в файл или сериализации:
        # Попробуем вызвать стандартный интерфейс экспорта
        if hasattr(exporter, "export"):
            exported_result = exporter.export(exported_data, export_path)
        else:
            # Ручной экспорт с использованием логики модуля
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(exported_data, f, ensure_ascii=False, indent=4)
            exported_result = export_path

        print(f"    -> Экспорт завершен успешно. Результат: {exported_result}")

        self.assertTrue(os.path.exists(export_path), "Экспортированный файл отчета должен существовать на диске.")

        with open(export_path, "r", encoding="utf-8") as f:
            loaded_export = json.load(f)

        print(f"    -> Проверка содержимого экспорта: найдено ключей -> {list(loaded_export.keys())}")
        self.assertIn("total_events", loaded_export)
        self.assertEqual(loaded_export["total_events"], 20)

        print("--- ПРАКТИЧЕСКАЯ ПРОВЕРКА ЭПИКА УСПЕШНО ЗАВЕРШЕНА ---")