import unittest
import uuid
import random
import os
import json
from skills.system_health_aggregator import SystemHealthAggregator
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.incident_aggregator import IncidentAggregator
from skills.dependency_audit_reporter import DependencyAuditReporter
from skills.recovery_dashboard_generator import RecoveryDashboardGenerator

class TestSystemHealthAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.aggregator = SystemHealthAggregator()
        self.recovery_hub = ErrorRecoveryHub()
        self.incident_aggregator = IncidentAggregator()
        self.audit_reporter = DependencyAuditReporter()
        self.dashboard_gen = RecoveryDashboardGenerator()
        
        self.test_module = f"module_{uuid.uuid4().hex[:8]}"
        self.incident_id = str(uuid.uuid4())
        self.error_msg = "ConnectionTimeout"
        self.traceback = "Traceback (most recent call last): File 'net.py', line 42"

    def test_full_health_cycle_integration(self):
        # 1. Имитация сбоя и агрегация инцидента
        incident_data = self.incident_aggregator.process_and_aggregate(
            self.test_module, self.error_msg, self.traceback, self.incident_id
        )
        self.assertIsNotNone(incident_data)

        # 2. Восстановление через Hub
        failure_analysis = self.recovery_hub.analyze_failure(self.incident_id)
        patch = self.recovery_hub.generate_patch(self.incident_id)
        recovery_status = self.recovery_hub.apply_patch(patch)
        self.assertTrue(recovery_status)

        # 3. Аудит зависимостей
        audit_payload = {"module": self.test_module, "status": "patched", "id": self.incident_id}
        report_str = self.audit_reporter.generate_report(audit_payload)
        self.assertIsInstance(report_str, str)

        # 4. Генерация комплексного дашборда здоровья
        metrics = {
            "stability_index": random.uniform(0.0, 1.0),
            "incident_count": 1
        }
        dashboard_path = f"dashboard_{self.incident_id}.json"
        
        dashboard_content = self.dashboard_gen.generate_dashboard(
            metrics, [incident_data], [report_str], "json"
        )
        
        export_success = self.dashboard_gen.export_dashboard(dashboard_content, dashboard_path)
        
        # Проверка реальных изменений
        self.assertTrue(export_success, "Дашборд не был экспортирован в файл")
        self.assertTrue(os.path.exists(dashboard_path), "Файл дашборда отсутствует на диске")
        
        with open(dashboard_path, 'r') as f:
            saved_data = json.load(f)
            self.assertEqual(saved_data['incident_id'], self.incident_id)

    def tearDown(self):
        # Очистка созданных файлов
        file_path = f"dashboard_{self.incident_id}.json"
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    unittest.main()