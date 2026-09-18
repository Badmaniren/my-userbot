import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.incident_forensics_compliance_checker import IncidentComplianceChecker

class TestIncidentComplianceChecker(unittest.TestCase):
    def setUp(self):
        self.checker = IncidentComplianceChecker()

    def test_evaluate_compliance_logic(self):
        # Генерация случайных данных для обеспечения непредсказуемости
        rand_id = uuid.uuid4().hex
        rand_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.log"
        rand_risk = random.randint(0, 20)
        rand_module = ''.join(random.choices(string.ascii_letters, k=10))

        incident_data = {
            "id": rand_id,
            "module_name": rand_module,
            "exception": "RuntimeError",
            "traceback_str": "Traceback: ..."
        }
        financial_data = {"risk_score": rand_risk}

        with patch('skills.incident_audit_trail_collector.collect_incident_audit_trail') as mock_audit:
            # Настройка мока аудита
            mock_audit.return_value = {"status": "success", "data": uuid.uuid4().hex}
            
            result = self.checker.evaluate_compliance(
                incident_data=incident_data,
                destination_path=rand_path,
                financial_data=financial_data
            )
            
            # Проверка логики соответствия
            expected_compliant = rand_risk < 10
            self.assertEqual(result["incident_id"], rand_id)
            self.assertEqual(result["compliant"], expected_compliant)
            self.assertEqual(result["risk_assessment"]["score"], rand_risk)
            mock_audit.assert_called_once()

    def test_evaluate_compliance_no_destination(self):
        # Тест пути без destination_path, но с audit_trail_path
        rand_id = uuid.uuid4().hex
        rand_audit_path = f"/tmp/{uuid.uuid4().hex}"

        result = self.checker.evaluate_compliance(
            incident_id=rand_id,
            audit_trail_path=rand_audit_path
        )

        self.assertEqual(result["audit_trail"]["path"], rand_audit_path)
        self.assertEqual(result["incident_id"], rand_id)

    def test_stream_compliance_package_integration(self):
        # Проверка передачи параметров в мост
        rand_id = uuid.uuid4().hex
        rand_impact = random.randint(100, 1000)
        financial_data = {"impact": rand_impact}
        rand_format = random.choice(["json", "xml", "pdf"])

        with patch.object(self.checker.bridge, 'stream_report_package') as mock_stream:
            mock_stream.return_value = b"random_binary_stream_data"

            response = self.checker.stream_compliance_package(
                incident_id=rand_id,
                financial_data=financial_data,
                format_type=rand_format
            )
            
            # Проверка, что мост получил именно те данные, которые мы передали
            mock_stream.assert_called_once_with(
                incident_id=rand_id,
                financial_data=financial_data,
                format_type=rand_format
            )
            self.assertEqual(response, b"random_binary_stream_data")

    def test_compliance_status_boundary(self):
        # Проверка пограничных значений риска
        low_risk = 9
        high_risk = 10

        res_low = self.checker.evaluate_compliance(financial_data={"risk_score": low_risk})
        res_high = self.checker.evaluate_compliance(financial_data={"risk_score": high_risk})

        self.assertEqual(res_low["compliance_status"], "COMPLIANT")
        self.assertEqual(res_high["compliance_status"], "NON_COMPLIANT")

if __name__ == '__main__':
    unittest.main()