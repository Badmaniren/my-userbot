import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
from skills.incident_sla_compliance_evaluator import IncidentSLAComplianceEvaluator

class TestIncidentSLAComplianceEvaluator(unittest.TestCase):

    def setUp(self):
        self.mock_sla_tracker = MagicMock()
        self.mock_telemetry = MagicMock()
        self.evaluator = IncidentSLAComplianceEvaluator(
            sla_tracker=self.mock_sla_tracker,
            telemetry_collector=self.mock_telemetry
        )

    def test_evaluate_compliance_rate_logic(self):
        # Генерируем хаотичные данные для проверки логики
        incident_id = uuid.uuid4().hex
        total_incidents = random.randint(10, 100)
        breached_incidents = random.randint(0, total_incidents)
        expected_rate = (total_incidents - breached_incidents) / total_incidents

        with patch('skills.incident_sla_compliance_evaluator.IncidentSLAComplianceEvaluator._fetch_historical_data') as mock_fetch:
            mock_fetch.return_value = {
                "total": total_incidents,
                "breached": breached_incidents,
                "id": incident_id
            }

            result = self.evaluator.evaluate_compliance_rate(incident_id)

            self.assertEqual(result['compliance_rate'], expected_rate)
            self.assertEqual(result['incident_ref'], incident_id)
            self.assertIsInstance(result['compliance_rate'], float)

    def test_telemetry_integration_with_random_payload(self):
        # Генерируем случайный набор метрик
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        metric_value = random.uniform(0.0, 1.0)

        with patch('skills.incident_sla_compliance_evaluator.IncidentSLAComplianceEvaluator._push_to_audit') as mock_audit:
            self.evaluator.report_telemetry(metric_name, metric_value)

            # Проверяем, что данные дошли до аудита без искажений
            mock_audit.assert_called_once()
            args, _ = mock_audit.call_args
            self.assertEqual(args[0], metric_name)
            self.assertEqual(args[1], metric_value)

    def test_sla_breach_prediction_handling(self):
        # Тестируем обработку потока данных через io.BytesIO
        random_id = uuid.uuid4().hex
        random_stream_content = f"{random_id}:{random.random()}".encode('utf-8')
        mock_stream = io.BytesIO(random_stream_content)

        with patch('skills.incident_sla_compliance_evaluator.IncidentSLAComplianceEvaluator._get_stream_source') as mock_source:
            mock_source.return_value = mock_stream

            prediction = self.evaluator.predict_next_breach_risk()

            # Проверяем, что парсер корректно извлек данные из потока
            self.assertIn(random_id[:5], prediction.get('debug_info', ''))
            self.assertTrue(0 <= prediction['risk_score'] <= 1)

    def test_audit_report_generation_integrity(self):
        # Проверка генерации отчета с рандомными идентификаторами
        report_id = uuid.uuid4().hex
        status = random.choice(['COMPLIANT', 'BREACHED', 'PENDING'])

        with patch('skills.incident_sla_compliance_evaluator.IncidentSLAComplianceEvaluator._write_to_audit_log') as mock_log:
            self.evaluator.generate_audit_report(report_id, status)

            mock_log.assert_called_once()
            call_args = mock_log.call_args[0][0]

            self.assertEqual(call_args['report_id'], report_id)
            self.assertEqual(call_args['status'], status)
            self.assertIsInstance(call_args['timestamp'], (int, float))

if __name__ == '__main__':
    unittest.main()