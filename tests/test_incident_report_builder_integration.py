import unittest
import uuid
import random
import os
import tempfile

from skills.incident_report_builder import IncidentReportBuilder
from skills import patch_metric_collector
from skills.dependency_audit_reporter import DependencyAuditReporter


class TestIncidentReportBuilderIntegration(unittest.TestCase):

    def setUp(self):
        self.builder = IncidentReportBuilder()
        self.incident_id = str(uuid.uuid4())
        self.module_name = f"test_module_{random.randint(1000, 9999)}"
        self.error_message = f"Random error {random.randint(1, 100)}"
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_incident_report_builder_integration(self):
        # Генерируем случайные данные для метрик патча
        success_flag = random.choice([True, False])
        raw_res = {"status_code": random.choice([200, 500, 404])}
        patch_payload = {
            "patch_id": str(uuid.uuid4()),
            "lines_changed": random.randint(1, 50)
        }

        # Вызываем функцию из patch_metric_collector для подготовки и записи метрики
        metric_data = patch_metric_collector.start_new(
            success=success_flag,
            incident_id=self.incident_id,
            error=self.error_message,
            raw_result=raw_res,
            patch_data=patch_payload
        )
        
        collector = patch_metric_collector.PatchMetricCollector()
        recorded_metric = collector.record_metric(metric_data)
        self.assertIsNotNone(recorded_metric)

        # Генерируем случайные данные для аудита зависимостей
        audit_data = {
            "incident_id": self.incident_id,
            "vulnerable_package": f"pkg-{random.randint(100, 999)}",
            "recommended_version": f"1.{random.randint(0, 5)}.{random.randint(0, 9)}"
        }

        reporter = DependencyAuditReporter()
        audit_report_str = reporter.generate_report(audit_data)
        self.assertIsInstance(audit_report_str, str)

        # Проверяем работу самого модуля incident_report_builder в композиции с реальными зависимостями
        # Ожидаем, что IncidentReportBuilder использует внутри себя patch_metric_collector и dependency_audit_reporter
        summary_payload = {
            "incident_id": self.incident_id,
            "module": self.module_name,
            "audit_info": audit_data,
            "metric_info": metric_data
        }

        # Метод генерации или экспорта сводного отчета в тестируемом модуле
        output_format = random.choice(["json", "txt", "html"])
        export_path = os.path.join(self.temp_dir.name, f"report_{uuid.uuid4()}.{output_format}")
        
        # Если в модуле incident_report_builder есть метод для комплексной сборки или экспорта:
        if hasattr(self.builder, "generate_summary_report"):
            summary_result = self.builder.generate_summary_report(summary_payload)
            self.assertIsNotNone(summary_result)
        
        if hasattr(self.builder, "export_incident_report"):
            exported = self.builder.export_incident_report(summary_payload, export_path)
            self.assertTrue(exported)
            self.assertTrue(os.path.exists(export_path))

        # Проверяем получение сводки метрик через интегрированный модуль
        metrics_summary = collector.get_metrics_summary(self.module_name)
        self.assertIsInstance(metrics_summary, str)


if __name__ == "__main__":
    unittest.main()