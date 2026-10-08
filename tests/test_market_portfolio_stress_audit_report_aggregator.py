import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.market_portfolio_stress_audit_report_aggregator import MarketPortfolioStressAuditReportAggregator

class TestMarketPortfolioStressAuditReportAggregator(unittest.TestCase):

    def setUp(self):
        self.db_storage = f"db://{uuid.uuid4().hex}"
        self.aggregator = MarketPortfolioStressAuditReportAggregator(self.db_storage)

    def test_aggregate_audit_report_flow(self):
        portfolio_id = uuid.uuid4().hex
        historical_window = random.randint(30, 365)
        expected_audit_id = uuid.uuid4().hex

        # Генерация случайных данных для матрицы
        mock_matrix_data = {
            "score": random.random(),
            "risk_level": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "token": uuid.uuid4().hex,
            "audit_id": expected_audit_id
        }

        with patch('skills.market_portfolio_stress_audit_report_aggregator.market_portfolio_stress_scenario_matrix_evaluator') as mock_evaluator:
            with patch('skills.market_portfolio_stress_audit_report_aggregator.market_portfolio_stress_audit_summary_vault') as mock_vault:

                # Настройка моков
                instance = mock_evaluator.MarketPortfolioStressScenarioMatrixEvaluator.return_value
                instance.evaluate_matrix.return_value = mock_matrix_data

                # Выполнение агрегации
                result = self.aggregator.aggregate(portfolio_id, historical_window)

                # Проверка вызовов
                instance.evaluate_matrix.assert_called_once_with(portfolio_id, historical_window)
                mock_vault.market_portfolio_stress_audit_summary_vault_process.assert_called_once()

                # Смысловой ассерт
                self.assertEqual(result['audit_id'], expected_audit_id)
                self.assertEqual(result['matrix_data']['token'], mock_matrix_data['token'])

    def test_audit_validation_integrity(self):
        storage_target = f"/tmp/{uuid.uuid4().hex}.json"
        expected_audit_id = uuid.uuid4().hex

        with patch('skills.market_portfolio_stress_audit_report_aggregator.market_portfolio_stress_audit_summary_vault') as mock_vault:
            mock_vault.market_portfolio_stress_audit_summary_vault_validate.return_value = True

            is_valid = self.aggregator.validate_report(storage_target, expected_audit_id)

            self.assertTrue(is_valid)
            mock_vault.market_portfolio_stress_audit_summary_vault_validate.assert_called_with(storage_target, expected_audit_id)

    def test_export_report_stream(self):
        storage_target = f"s3://bucket/{uuid.uuid4().hex}"
        export_format = random.choice(['json', 'pdf', 'csv'])
        random_content = ''.join(random.choices(string.ascii_letters, k=20)).encode()

        with patch('skills.market_portfolio_stress_audit_report_aggregator.market_portfolio_stress_audit_summary_vault') as mock_vault:
            mock_vault.market_portfolio_stress_audit_summary_vault_export.return_value = io.BytesIO(random_content)

            stream = self.aggregator.export_report(storage_target, export_format)

            self.assertEqual(stream.read(), random_content)
            mock_vault.market_portfolio_stress_audit_summary_vault_export.assert_called_once_with(storage_target, export_format)

    def test_anomaly_detection_logic(self):
        scenario_token = uuid.uuid4().hex
        threshold = random.uniform(0.1, 0.9)
        expected_bool = random.choice([True, False])

        with patch('skills.market_portfolio_stress_audit_report_aggregator.market_portfolio_stress_scenario_matrix_evaluator') as mock_evaluator:
            instance = mock_evaluator.MarketPortfolioStressScenarioMatrixEvaluator.return_value
            instance.detect_matrix_anomalies.return_value = expected_bool

            result = self.aggregator.check_anomalies(scenario_token, threshold)

            self.assertEqual(result, expected_bool)
            instance.detect_matrix_anomalies.assert_called_with(scenario_token, threshold)

if __name__ == '__main__':
    unittest.main()
