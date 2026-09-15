import unittest
import uuid
import random
import os
import tempfile
from skills.system_health_audit_pipeline import SystemHealthAuditPipeline

class TestSystemHealthAuditPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.pipeline = SystemHealthAuditPipeline()
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_pipeline_composition_and_execution(self):
        unique_module_name = f"module_{uuid.uuid4().hex[:8]}"
        random_cpu_load = round(random.uniform(10.0, 99.9), 2)
        random_memory_usage = round(random.uniform(20.0, 95.5), 2)
        
        incident_data = {
            "incident_id": str(uuid.uuid4()),
            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "description": f"Random test incident {uuid.uuid4().hex[:6]}"
        }
        
        audit_summary = {
            "audit_id": str(uuid.uuid4()),
            "status": "PASSED" if random.choice([True, False]) else "WARNING"
        }
        
        metrics = {
            "cpu_load": random_cpu_load,
            "memory_usage": random_memory_usage,
            "active_connections": random.randint(10, 500)
        }
        
        dashboard_format = random.choice(["json", "html", "yaml"])
        
        incidents_list = [
            {
                "id": str(uuid.uuid4()),
                "code": random.randint(500, 599)
            }
        ]
        
        patches_list = [
            {
                "patch_id": str(uuid.uuid4()),
                "applied": random.choice([True, False])
            }
        ]
        
        report_file_path = os.path.join(self.test_dir.name, f"report_{uuid.uuid4().hex}.json")
        dashboard_file_path = os.path.join(self.test_dir.name, f"dashboard_{uuid.uuid4().hex}.json")

        result = self.pipeline.run_audit_pipeline(
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

        self.assertIsNotNone(result, "Пайпалайн аудита не должен возвращать None")
        self.assertIsInstance(result, dict, "Результат выполнения должен быть словарем")

        self.assertTrue(
            os.path.exists(report_file_path), 
            f"Файл отчета должен быть создан по пути: {report_file_path}"
        )
        self.assertTrue(
            os.path.exists(dashboard_file_path), 
            f"Файл дашборда должен быть создан по пути: {dashboard_file_path}"
        )

        self.assertIn("telemetry", result, "Результат должен содержать данные телеметрии")
        self.assertIn("aggregation", result, "Результат должен содержать агрегированные данные")

if __name__ == "__main__":
    unittest.main()