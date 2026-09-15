import unittest
import uuid
import random
import os
import tempfile
from skills.system_health_reporter import SystemHealthReporter
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.incident_aggregator import IncidentAggregator
from skills.dependency_audit_reporter import DependencyAuditReporter
from skills.recovery_dashboard_generator import RecoveryDashboardGenerator

class TestSystemHealthReporterIntegration(unittest.TestCase):

    def setUp(self):
        self.reporter = SystemHealthHealthReporter = SystemHealthReporter()
        self.recovery_hub = ErrorRecoveryHub()
        self.incident_aggregator = IncidentAggregator()
        self.dependency_reporter = DependencyAuditReporter()
        self.dashboard_generator = RecoveryDashboardGenerator()
        
        self.test_module = f"test_module_{uuid.uuid4().hex[:8]}"
        self.incident_id = str(uuid.uuid4())
        self.random_error_msg = f"Random error {uuid.uuid4()}"

    def test_comprehensive_system_health_pipeline(self):
        try:
            raise RuntimeError(self.random_error_msg)
        except RuntimeError as e:
            tb_str = "Traceback (most recent call last):\n  File 'test.py', line 10\n    raise RuntimeError"
            
            # Шаг 1: Захват и агрегация реального инцидента через смежные модули без моков
            captured_incident = self.recovery_hub.capture_failure(self.test_module, e, tb_str)
            aggregated_data = self.incident_aggregator.process_and_aggregate(
                self.test_module, e, tb_str, self.incident_id
            )
            
            self.assertIsNotNone(aggregated_data)

            # Шаг 2: Формирование аудита зависимостей для отчета о здоровье
            audit_payload = {
                "epic_id": str(uuid.uuid4()),
                "status": "checked",
                "vulnerabilities": random.randint(0, 5),
                "module": self.test_module
            }
            dependency_report_str = self.dependency_reporter.generate_report(audit_payload)
            self.assertIsInstance(dependency_report_str, str)

            # Шаг 3: Сбор метрик для дашборда
            dashboard_metrics = self.dashboard_generator.aggregate_system_health()
            self.assertIsInstance(dashboard_metrics, dict)

            # Шаг 4: Генерация комплексного отчета через тестируемый модуль SystemHealthReporter
            # Передаем реальные сгенерированные данные
            health_report = self.reporter.generate_health_report(
                module_name=self.test_module,
                incident_data=aggregated_data,
                audit_summary=dependency_report_str,
                metrics=dashboard_metrics
            )
            
            self.assertIsNotNone(health_report)
            
            # Шаг 5: Проверка экспорта отчета в файл со случайным путем
            with tempfile.TemporaryDirectory() as tmpdir:
                export_filename = f"health_report_{uuid.uuid4().hex}.json"
                export_path = os.path.join(tmpdir, export_filename)
                
                export_result = self.reporter.export_health_report(health_report, export_path)
                self.assertTrue(export_result)
                self.assertTrue(os.path.exists(export_path))
                
                with open(export_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    self.assertIn(self.test_module, file_content)

if __name__ == '__main__':
    unittest.main()