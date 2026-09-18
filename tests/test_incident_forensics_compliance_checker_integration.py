import unittest
import os
import shutil
import uuid
import random
from skills.incident_forensics_compliance_checker import check_incident_compliance
from skills.incident_audit_trail_collector import collect_incident_audit_trail
from skills.incident_forensics_report_bridge import IncidentForensicsReportBridge

class TestIncidentForensicsComplianceCheckerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"./test_sandbox_{uuid.uuid4()}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.incident_id = str(uuid.uuid4())
        self.module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.destination_path = os.path.join(self.test_dir, f"audit_{self.incident_id}.json")
        self.export_path = os.path.join(self.test_dir, f"forensics_report_{self.incident_id}.json")
        
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_compliance_checker_composition(self):
        incident_data = {
            "incident_id": self.incident_id,
            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "description": f"Random security incident {uuid.uuid4()}",
            "telemetry": {"cpu_usage": random.uniform(50.0, 100.0)}
        }
        
        financial_data = {
            "loss_amount": round(random.uniform(1000.0, 50000.0), 2),
            "currency": "USD"
        }

        # Вызываем реальные интегрированные модули для подготовки данных
        collect_incident_audit_trail(
            incident_data=incident_data,
            destination_path=self.destination_path,
            include_raw_telemetry=True
        )
        
        self.assertTrue(os.path.exists(self.destination_path), "Audit trail collector должен создать файл аудита.")

        # Вызываем целевой модуль, проверяя отсутствие моков и реальное взаимодействие
        compliance_result = check_incident_compliance(
            incident_id=self.incident_id,
            incident_data=incident_data,
            audit_trail_path=self.destination_path,
            financial_data=financial_data,
            export_path=self.export_path,
            format_type="json"
        )

        self.assertIsInstance(compliance_result, dict, "Результат должен быть словарем.")
        self.assertIn("compliance_status", compliance_result, "Ответ должен содержать статус соответствия.")
        self.assertEqual(compliance_result.get("incident_id"), self.incident_id, "ID инцидента должен совпадать.")
        
        # Проверяем, что отчет форензика также был сформирован в рамках композиции
        self.assertTrue(os.path.exists(self.export_path), "Форензик-отчет должен быть сгенерирован целевым модулем.")

if __name__ == "__main__":
    unittest.main()