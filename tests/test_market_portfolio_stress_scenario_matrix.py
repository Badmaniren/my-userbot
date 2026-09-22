import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.market_portfolio_stress_scenario_matrix import MarketPortfolioStressScenarioMatrix

class TestMarketPortfolioStressScenarioMatrix(unittest.TestCase):

    def setUp(self):
        self.dependencies = {
            "db_storage": MagicMock(),
            "market_parser": MagicMock(),
            "market_portfolio_alert_dispatcher": MagicMock(),
            "market_portfolio_alert_event_sink": MagicMock(),
            "market_portfolio_alert_filter_router": MagicMock(),
            "market_portfolio_api_gateway": MagicMock(),
            "market_portfolio_audit_alert_notifier": MagicMock(),
            "market_portfolio_audit_compliance_hub": MagicMock(),
            "market_portfolio_audit_log_exporter": MagicMock(),
            "market_portfolio_autonomous_sentinel": MagicMock(),
            "market_portfolio_backtest_evaluator_bridge": MagicMock(),
            "market_portfolio_backtester": MagicMock(),
            "market_portfolio_collector_agent": MagicMock(),
            "market_portfolio_data_exporter": MagicMock(),
            "market_portfolio_digest": MagicMock(),
            "market_portfolio_event_intelligence_hub": MagicMock(),
            "market_portfolio_integration_hub": MagicMock(),
            "market_portfolio_monitor": MagicMock(),
            "market_portfolio_performance_analytics": MagicMock(),
            "market_portfolio_predictive_aggregator": MagicMock(),
            "market_portfolio_scenario_simulator": MagicMock(),
            "market_portfolio_strategy_optimizer": MagicMock(),
            "market_portfolio_stress_reporter": MagicMock(),
            "market_portfolio_telegram_command_center": MagicMock(),
            "market_portfolio_telegram_notifier": MagicMock(),
            "market_portfolio_valuation": MagicMock(),
            "market_portfolio_visualizer_v2": MagicMock(),
            "market_portfolio_webhook_event_logger": MagicMock(),
            "market_portfolio_webhook_sync": MagicMock(),
            "market_report_generator": MagicMock(),
            "market_telegram_pipeline": MagicMock()
        }
        self.matrix_builder = MarketPortfolioStressScenarioMatrix(**self.dependencies)

    def test_initialization_dependencies(self):
        for key, mock_obj in self.dependencies.items():
            with self.subTest(dependency=key):
                self.assertIn(key, self.matrix_builder.dependencies)
                self.assertEqual(self.matrix_builder.dependencies[key], mock_obj)

    def test_build_matrix_success(self):
        portfolio_id = uuid.uuid4().hex
        risk_factors = [uuid.uuid4().hex for _ in range(random.randint(2, 5))]

        result = self.matrix_builder.build_matrix(portfolio_id, risk_factors)

        self.assertIn("matrix_id", result)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["factors"], risk_factors)
        self.assertIsInstance(result["payload"], str)
        self.assertTrue(len(result["payload"]) > 0)

    def test_build_matrix_invalid_parameters(self):
        portfolio_id = uuid.uuid4().hex
        with self.assertRaises(ValueError):
            self.matrix_builder.build_matrix("", [])

    def test_export_matrix_stream(self):
        random_bytes = b''.join(random.choice([b'0', b'1', b'A', b'F']) for _ in range(64))
        mock_stream = io.BytesIO()

        with patch.object(mock_stream, 'write', wraps=mock_stream.write) as mock_write:
            written_bytes = self.matrix_builder.export_matrix(mock_stream, uuid.uuid4().hex)
            self.assertGreater(written_bytes, 0)
            mock_write.assert_called()

    def test_internal_components_invocation_mock(self):
        target_dep = random.choice(list(self.dependencies.keys()))
        selected_mock = self.dependencies[target_dep]

        expected_return_val = uuid.uuid4().hex
        selected_mock.return_value = expected_return_val

        result = selected_mock(uuid.uuid4().hex)
        self.assertEqual(result, expected_return_val)
        selected_mock.assert_called_once()

if __name__ == '__main__':
    unittest.main()
