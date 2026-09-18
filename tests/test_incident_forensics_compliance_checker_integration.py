import unittest
import os
import uuid
import json
import tempfile
import shutil
from skills.incident_forensics_compliance_checker import IncidentComplianceChecker

class TestIncidentComplianceCheckerIntegration(unittest.TestCase):
    def setUp(self):
        self.checker = IncidentComplianceChecker()
        self.test_dir = tempfile.mkdtemp()
        self.incident_id = str(uuid.uuid4())
        self.incident_data = {
            "id": self.incident_id,
            "module_name": "auth_service",
            "exception": "AccessDenied",
            "traceback_str": "Traceback at line 42"
        }
        self.financial_data = {
            "risk_score": 5,
            "impact": 100
        }
        self.export_path = os.path.join(self.test_dir, f"report_{self.incident_id}.json")
        self.audit_path = os.path.join(self.test_dir, "audit_logs")
        os.makedirs(self.audit_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_evaluate_compliance_full_integration(self):
        # Выполнение реального процесса
        result = self.checker.evaluate_compliance(
            incident_data=self.incident_data,
            destination_path=self.audit_path,
            financial_data=self.financial_data,
            export_path=self.export_path,
            format_type="json"
        )

        # Проверка корректности возвращаемых данных
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertEqual(result["compliance_status"], "COMPLIANT")
        self.assertTrue(result["compliant"])
        self.assertEqual(result["risk_assessment"]["score"], 5)

        # Проверка создания файла отчета (интеграция с bridge)
        self.assertTrue(os.path.exists(self.export_path), "Отчет не был создан на диске")
        
        with open(self.export_path, 'r') as f:
            report_content = json.load(f)
            self.assertEqual(report_content.get("incident_id"), self.incident_id)

        # Проверка аудита (интеграция с collector)
        self.assertIn("path", result["audit_trail"])
        self.assertTrue(os.path.exists(result["audit_trail"]["path"]))

    def test_non_compliant_risk_threshold(self):
        high_risk_data = {"risk_score": 50}
        result = self.checker.evaluate_compliance(
            incident_data=self.incident_data,
            financial_data=high_risk_data
        )
        
        self.assertEqual(result["compliance_status"], "NON_COMPLIANT")
        self.assertFalse(result["compliant"])
        self.assertEqual(result["risk_assessment"]["score"], 50)

    def test_stream_compliance_package_integration(self):
        # Проверка потоковой передачи через bridge
        stream_result = self.checker.stream_compliance_package(
            incident_id=self.incident_id,
            financial_data=self.financial_data,
            format_type="json"
        )
        
        # Проверяем, что bridge вернул структуру данных, а не None
        self.assertIsNotNone(stream_result)
        # Если bridge возвращает путь к потоку или объект, проверяем наличие ключа
        if isinstance(stream_result, dict):
            self.assertIn("incident_id", stream_result)
            self.assertEqual(stream_result["incident_id"], self.incident_id)

if __name__ == '__main__':
    unittest.main()