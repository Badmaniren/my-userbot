import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import string
from skills.market_portfolio_macro_liquidity_v2 import start_new

class TestMarketPortfolioMacroLiquidityV2(unittest.TestCase):

    def setUp(self):
        self.random_hex = uuid.uuid4().hex
        self.random_int = random.randint(1000, 999999)
        self.random_float = random.uniform(1.0, 1000.0)
        self.random_string = ''.join(random.choices(string.ascii_letters, k=12))
        
        self.dependencies = {
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
            "market_portfolio_liquidity_scenario_analyzer": MagicMock(),
            "market_portfolio_monitor": MagicMock(),
            "market_portfolio_performance_analytics": MagicMock(),
            "market_portfolio_predictive_aggregator": MagicMock(),
            "market_portfolio_scenario_simulator": MagicMock(),
            "market_portfolio_slippage_model": MagicMock(),
            "market_portfolio_strategy_optimizer": MagicMock(),
            "market_portfolio_stress_audit_visualizer": MagicMock(),
            "market_portfolio_stress_monte_carlo_engine": MagicMock(),
            "market_portfolio_stress_recovery_coordinator_bridge": MagicMock(),
            "market_portfolio_stress_reporter": MagicMock(),
            "market_portfolio_stress_scenario_pipeline": MagicMock(),
            "market_portfolio_tax_calculator": MagicMock(),
            "market_portfolio_telegram_command_center": MagicMock(),
            "market_portfolio_telegram_notifier": MagicMock(),
            "market_portfolio_valuation": MagicMock(),
            "market_portfolio_var_liquidity_core": MagicMock(),
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

    def test_start_new_execution_flow(self):
        expected_result = f"macro_liquidity_{self.random_hex}"
        self.dependencies["market_portfolio_var_liquidity_core"].compute.return_value = expected_result

        result = start_new(self.dependencies)
        
        self.dependencies["market_portfolio_var_liquidity_core"].compute.assert_called_once()
        self.assertEqual(result, expected_result)

    def test_start_new_handles_io_stream_processing(self):
        garbage_bytes = self.random_string.encode('utf-8')
        mock_stream = io.BytesIO(garbage_bytes)

        with patch('skills.market_portfolio_macro_liquidity_v2.open', return_value=mock_stream, create=True) as mock_open:
            self.dependencies["market_portfolio_collector_agent"].fetch_stream.return_value = mock_stream
            
            result = start_new(self.dependencies)
            
            self.assertIsNotNone(result)
            mock_open.assert_not_called()

    def test_start_new_with_anomaly_detection_failure(self):
        error_message = f"anomaly_fault_{self.random_hex}"
        self.dependencies["market_anomaly_detector"].detect.side_effect = ValueError(error_message)

        with self.assertRaises(ValueError) as ctx:
            start_new(self.dependencies)

        self.assertIn(error_message, str(ctx.exception))

    def test_start_new_passes_random_weights(self):
        custom_payload = {
            "token": self.random_hex,
            "threshold": self.random_float,
            "limit": self.random_int
        }
        
        self.dependencies["market_portfolio_strategy_optimizer"].optimize.return_value = custom_payload

        with patch('skills.market_portfolio_macro_liquidity_v2.uuid.uuid4', return_value=uuid.UUID(self.random_hex)) as mock_uuid:
            res = start_new(self.dependencies)
            self.assertIsNotNone(res)

if __name__ == '__main__':
    unittest.main()