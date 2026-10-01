import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.market_portfolio_stress_stress_matrix_builder import start_new

class TestMarketPortfolioStressStressMatrixBuilder(unittest.TestCase):

    def setUp(self):
        self.random_hex = uuid.uuid4().hex
        self.random_string = ''.join(random.choices(string.ascii_letters, k=12))
        self.random_float = random.uniform(10.0, 999.9)
        self.random_int = random.randint(1, 10000)

        self.mock_deps = {
            "db_storage": MagicMock(),
            "extractor_tool_1790087207": MagicMock(),
            "extractor_tool_1790102839": MagicMock(),
            "extractor_tool_1790262909": MagicMock(),
            "extractor_tool_1790621808": MagicMock(),
            "market_anomaly_detector": MagicMock(),
            "market_insider_activity_tracker": MagicMock(),
            "market_insider_alert_pipeline": MagicMock(),
            "market_insider_anomaly_analyzer": MagicMock(),
            "market_insider_anomaly_report_bridge": MagicMock(),
            "market_news_sentiment_analyzer": MagicMock(),
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
            "market_portfolio_dividend_tracker": MagicMock(),
            "market_portfolio_event_intelligence_hub": MagicMock(),
            "market_portfolio_execution_cost_optimizer": MagicMock(),
            "market_portfolio_execution_pipeline": MagicMock(),
            "market_portfolio_integration_hub": MagicMock(),
            "market_portfolio_monitor": MagicMock(),
            "market_portfolio_performance_analytics":     MagicMock(),
            "market_portfolio_predictive_aggregator": MagicMock(),
            "market_portfolio_scenario_simulator": MagicMock(),
            "market_portfolio_slippage_model": MagicMock(),
            "market_portfolio_strategy_optimizer": MagicMock(),
            "market_portfolio_stress_monte_carlo_engine": MagicMock(),
            "market_portfolio_stress_recovery_coordinator_bridge": MagicMock(),
            "market_portfolio_stress_reporter": MagicMock(),
            "market_portfolio_stress_scenario_pipeline": MagicMock(),
            "market_portfolio_tax_calculator": MagicMock(),
            "market_portfolio_telegram_command_center": MagicMock(),
            "market_portfolio_telegram_notifier": MagicMock(),
            "market_portfolio_valuation": MagicMock(),
            "market_portfolio_visualizer_v2": MagicMock(),
            "market_portfolio_webhook_event_logger": MagicMock(),
            "market_portfolio_webhook_sync": MagicMock(),
            "market_report_generator": MagicMock(),
            "market_sentiment_digest": MagicMock(),
            "market_sentiment_risk_alert_bridge": MagicMock(),
            "market_sentiment_risk_hub": MagicMock(),
            "market_sentiment_telegram_publisher": MagicMock(),
            "market_telegram_pipeline": MagicMock()
        }

    def test_start_new_success_execution(self):
        expected_result_key = self.random_hex
        expected_value = self.random_float

        self.mock_deps["market_portfolio_scenario_simulator"].simulate.return_value = {
            expected_result_key: expected_value
        }

        with patch('skills.market_portfolio_stress_stress_matrix_builder.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = self.random_hex
            
            result = start_new(
                portfolio_id=self.random_hex,
                liquidity_shock_factor=self.random_float,
                **self.mock_deps
            )

        self.assertIsNotNone(result)
        self.mock_deps["market_portfolio_scenario_simulator"].simulate.assert_called_once()

    def test_start_new_handles_io_stream(self):
        stream_data = io.BytesIO(f"{self.random_string}_{self.random_int}".encode('utf-8'))
        
        self.mock_deps["db_storage"].read_stream.return_value = stream_data

        with patch('skills.market_portfolio_stress_stress_matrix_builder.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = self.random_hex
            
            result = start_new(
                portfolio_id=self.random_hex,
                liquidity_shock_factor=self.random_float,
                **self.mock_deps
            )

        self.assertIsNotNone(result)
        self.mock_deps["db_storage"].read_stream.assert_called_once()

    def test_start_new_exception_handling(self):
        self.mock_deps["market_portfolio_stress_monte_carlo_engine"].run.side_effect = Exception(self.random_string)

        with patch('skills.market_portfolio_stress_stress_matrix_builder.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = self.random_hex
            
            with self.assertRaises(Exception) as context:
                start_new(
                    portfolio_id=self.random_hex,
                    liquidity_shock_factor=self.random_float,
                    **self.mock_deps
                )
            
            self.assertIn(self.random_string, str(context.exception))

if __name__ == '__main__':
    unittest.main()