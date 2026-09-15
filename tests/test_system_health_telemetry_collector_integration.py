import unittest
import os
import uuid
import random
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector

class TestSystemHealthTelemetryCollectorIntegration(unittest.TestCase):
    def setUp(self):
        self.collector = SystemHealthTelemetryCollector()
        self.test_dir = f"test_telemetry_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                except OSError:
                    pass
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except OSError:
                    pass
        try:
            os.rmdir(self.test_dir)
        except OSError:
            pass

    def test_full_telemetry_composition_pipeline(self):
        unique_module_name = f"module_{uuid.uuid4().hex[:8]}"
        random_metric_value = random.randint(100, 9999)
        random_incident_id = str(uuid.uuid4())

        incident_data = {
            "incident_id": random_incident_id,
            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "status": "active"
        }
        
        audit_summary = {
            "audit_id": uuid.uuid4().hex,
            "passed": random.choice([True, False])
        }

        metrics = {
            "cpu_load": random.uniform(10.0, 99.0),
            "memory_usage": random_metric_value
        }

        incidents_list = [incident_data]
        patches_list = [{"patch_id": uuid.uuid4().hex, "status": "applied"}]
        dashboard_format = random.choice(["json", "html"])
        
        report_file_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.json")
        dashboard_file_path = os.path.join(self.test_dir, f"dashboard_{uuid.uuid4().hex}.json")

        result = self.collector.collect_and_process_telemetry(
            module_name=unique_module_name,
            incident_data=incident_data,
            audit_summary=audit_summary,
            metrics=metrics,
            dashboard_format=dashboard_format,
            incidents_list=incidents_list,
            patches_list=patches_list,
            report_path=report_file_path,
            dashboard_path=dashboard_file_path
        )

        self.assertIsNotNone(result, "Интеграционный метод должен возвращать результат работы композиции навыков.")
        
        self.assertTrue(
            os.path.exists(report_file_path),
            f"Файл отчета о здоровье системы должен быть создан по пути: {report_file_path}"
        )
        
        self.assertTrue(
            os.path.exists(dashboard_file_path),
            f"Файл дашборда системы должен быть создан по пути: {dashboard_file_path}"
        )

        if isinstance(result, dict):
            self.assertIn(unique_module_name, str(result), "Результат должен содержать переданное имя модуля.")

if __name__ == "__main__":
    unittest.main()