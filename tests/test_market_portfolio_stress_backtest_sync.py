import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

from skills.market_portfolio_stress_backtest_sync import start_new


class TestMarketPortfolioStressBacktestSync(unittest.TestCase):

    def setUp(self):
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
            "market_portfolio_monitor": MagicMock(),
            "market_portfolio_performance_analytics": MagicMock(),
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
            "market_portfolio_var_liquidity_core": "market_portfolio_var_liquidity_core",
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

    def test_start_new_success_flow(self):
        expected_sync_id = uuid.uuid4().hex
        random_payload = bytes(''.join(random.choices(string.ascii_letters + string.digits, k=64)), 'utf-8')
        mock_io_stream = io.BytesIO(random_payload)

        with patch('skills.market_portfolio_stress_backtest_sync.market_portfolio_backtester') as mock_backtester, \
             patch('skills.market_portfolio_stress_backtest_sync.market_portfolio_stress_scenario_pipeline') as mock_pipeline:
            
            mock_backtester.sync_results.return_value = expected_sync_id
            mock_pipeline.fetch_stream.return_value = mock_io_stream

            result = start_new(self.dependencies)

            self.assertEqual(result, expected_sync_id)
            mock_backtester.sync_results.assert_called_once()
            mock_pipeline.fetch_stream.assert_called_once()

    def test_start_new_handles_malformed_stream(self):
        random_garbage = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)

        with patch('skills.market_portfolio_stress_backtest_sync.market_portfolio_backtester') as mock_backtester, \
             patch('skills.market_portfolio_stress_backtest_sync.market_portfolio_stress_scenario_pipeline') as mock_pipeline:

            mock_backtester.sync_results.side_effect = ValueError(uuid.uuid4().hex)
            mock_pipeline.fetch_stream.return_value = random_garbage

            with self.assertRaises(ValueError):
                start_new(self.dependencies)

    def test_start_new_integrates_components(self):
        random_metric_name = uuid.uuid4().hex
        random_threshold = random.uniform(1.0, 100.0)

        with patch('skills.market_portfolio_stress_backtest_sync.market_portfolio_performance_analytics') as mock_perf:
            mock_perf.evaluate_predictive_power.return_value = {random_metric_name: random_threshold}

            res = start_new(self.dependencies)
            
            self.assertIsNotNone(res)
            mock_perf.evaluate_predictive_power.assert_called_once()