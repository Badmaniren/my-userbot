import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from skills.market_portfolio_stress_deep_impact_analyzer import start_new


class TestMarketPortfolioStressDeepImpactAnalyzer(unittest.TestCase):

    def setUp(self):
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
            "market_portfolio_liquidity_scenario_analyzer": MagicMock(),
            "market_portfolio_monitor": MagicMock(),
            "market_portfolio_performance_analytics": MagicMock(),
            "market_portfolio_predictive_aggregator": MagicMock(),
            "market_portfolio_scenario_simulator": MagicMock(),
            "market_portfolio_slippage_model": MagicMock(),
            "market_portfolio_strategy_optimizer": MagicMock(),
            "market_portfolio_stress_audit_visualizer": MagicMock(),
            "market_portfolio_stress_auto_rebalance_trigger": MagicMock(),
            "market_portfolio_stress_monte_carlo_engine": MagicMock(),
            "market_portfolio_stress_recovery_coordinator_bridge": MagicMock(),
            "market_portfolio_stress_reporter": MagicMock(),
            "market_portfolio_stress_scenario_matrix_evaluator": MagicMock(),
            "market_portfolio_stress_scenario_pipeline":`MagicMock(),
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
        random_shock_id = uuid.uuid4().hex
        random_intensity = random.uniform(10.0, 999.9)
        random_stream_data = ''.join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')

        self.mock_deps["market_portfolio_stress_monte_carlo_engine"].run_simulation.return_value = {
            "shock_id": random_shock_id,
            "impact_score": random_intensity
        }

        with patch('skills.market_portfolio_stress_deep_impact_analyzer.io.BytesIO', return_value=io.BytesIO(random_stream_data)) as mock_io:
            result = start_new(self.mock_deps)

            self.assertIsNotNone(result)
            self.mock_deps["market_portfolio_stress_monte_carlo_engine"].run_simulation.assert_called()

    def test_start_new_handles_anomaly_detection(self):
        expected_anomaly_flag = random.choice([True, False])
        random_tag = uuid.uuid4().hex

        self.mock_deps["market_anomaly_detector"].detect.return_value = {
            "anomaly_detected": expected_anomaly_flag,
            "tag": random_tag
        }

        with patch.object(self.mock_deps["db_storage"], 'save') as mock_save:
            start_new(self.mock_deps)
            mock_save.assert_called()

    def test_start_new_error_propagation(self):
        random_error_message = uuid.uuid4().hex
        self.mock_deps["market_portfolio_scenario_simulator"].simulate.side_effect = RuntimeError(random_error_message)

        with self.assertRaises(RuntimeError) as context:
            start_new(self.mock_deps)

        self.assertIn(random_error_message, str(context.exception))


if __name__ == '__main__':
    unittest.main()