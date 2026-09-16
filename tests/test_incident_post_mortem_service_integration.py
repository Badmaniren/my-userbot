import unittest
import uuid
import random
import os
from skills.incident_post_mortem_service import IncidentPostMortemService
from skills.incident_aggregator import IncidentAggregator
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.recovery_report_exporter import RecoveryReportExporter

class TestIncidentPostMortemServiceIntegration(unittest.TestCase):
    def setUp(self):
        self.service = IncidentPostMortemService()
        self.aggregator = IncidentAggregator()
        self.hub = ErrorRecoveryHub()
        self.exporter = RecoveryReportExporter()
        self.test_incident_id = str(uuid.uuid4())

    def test_full_lifecycle_integration(self):
        # Генерируем случайные данные для инцидента
        random_timeout = random.randint(10, 500)
        random_memory = random.randint(100, 2048)
        incident_data = {
            "incident_id": self.test_incident_id,
            "error_code": f"ERR-{random.randint(1000, 9999)}",
            "metrics": {
                "memory_leak_mb": random_memory,
                "timeout_count": random_timeout
            }
        }
        
        recovery_payload = {
            "logs": f"System recovery initiated at {random.randint(1, 100)}s\nCritical failure resolved."
        }

        # Выполняем генерацию отчета через сервис
        report = self.service.generate_report(incident_data, recovery_payload)

        # Проверка целостности данных
        self.assertEqual(report["incident_id"], self.test_incident_id)
        self.assertIn(str(random_timeout), report["root_cause_analysis"])
        self.assertIn(incident_data["error_code"], report["root_cause_analysis"])
        self.assertIsInstance(report["report_id"], str)
        self.assertTrue(len(report["report_id"]) > 0)

    def test_batch_historical_processing(self):
        # Генерация пакета случайных инцидентов
        batch_size = random.randint(3, 7)
        batch = []
        for _ in range(batch_size):
            batch.append({
                "incident_id": str(uuid.uuid4()),
                "metrics": {"timeout_count": random.randint(1, 10)}
            })

        # Обработка массовых данных
        reports = self.service.import_historical_data(batch)

        # Проверка корректности обработки
        self.assertEqual(len(reports), batch_size)
        self.assertNotEqual(reports[0]["incident_id"], reports[1]["incident_id"])
        
        # Проверка аналитики
        summary = self.service.export_summary_analytics(batch)
        self.assertEqual(summary["total_incidents"], batch_size)
        self.assertEqual(len(summary["reports_summary"]), batch_size)

    def test_data_persistence_flow(self):
        # Проверка сквозного прохождения через реальные компоненты
        incident_id = str(uuid.uuid4())
        
        # Вызов метода, который обращается к реальным методам зависимых навыков
        report = self.service.generate_report(incident_id)
        
        # Проверяем, что отчет содержит данные, полученные из реальных агрегаторов
        self.assertIn("incident_id", report)
        self.assertEqual(report["incident_id"], incident_id)
        self.assertIn("metrics_snapshot", report)
        self.assertIn("recovery_logs_summary", report)

if __name__ == "__main__":
    unittest.main()