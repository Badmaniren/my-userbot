import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import sys

from skills.market_portfolio_rebalance_engine import start_new, MarketPortfolioRebalanceEngine


class TestMarketPortfolioRebalanceEngine(unittest.TestCase):

    def setUp(self):
        self.required_keys = [
            "db_storage",
            "extractor_tool_1790087207",
            "extractor_tool_1790102839",
            "extractor_tool_1790262909",
            "market_anomaly_detector",
            "market_insider_activity_tracker",
            "market_insider_alert_pipeline",
            "market_insider_anomaly_analyzer",
            "market_insider_anomaly_report_bridge",
            "market_news_sentiment_analyzer",
            "market_parser",
            "market_portfolio_alert_dispatcher",
            "market_portfolio_alert_event_sink",
            "market_portfolio_alert_filter_router",
            "market_portfolio_api_gateway",
            "market_portfolio_audit_alert_notifier",
            "market_portfolio_audit_compliance_hub",
            "market_portfolio_audit_log_exporter",
            "market_portfolio_autonomous_sentinel",
            "market_portfolio_backtest_evaluator_bridge",
            "market_portfolio_backtester",
            "market_portfolio_collector_agent",
            "market_portfolio_data_exporter",
            "market_portfolio_digest",
            "market_portfolio_event_intelligence_hub",
            "market_portfolio_integration_hub",
            "market_portfolio_monitor",
            "market_portfolio_performance_analytics",
            "market_portfolio_predictive_aggregator",
            "market_portfolio_scenario_simulator",
            "market_portfolio_strategy_optimizer",
            "market_portfolio_stress_reporter",
            "market_portfolio_stress_scenario_pipeline",
            "market_portfolio_telegram_command_center",
            "market_portfolio_telegram_notifier",
            "market_portfolio_valuation",
            "market_portfolio_visualizer_v2",
            "market_portfolio_webhook_event_logger",
            "market_portfolio_webhook_sync",
            "market_report_generator",
            "market_sentiment_digest",
            "market_sentiment_risk_alert_bridge",
            "market_sentiment_risk_hub",
            "market_sentiment_telegram_publisher",
            "market_telegram_pipeline"
        ]

    def test_start_new_missing_dependency(self):
        bad_key = random.choice(self.required_keys)
        deps = {k: MagicMock() for k in self.required_keys if k != bad_key}
        with self.assertRaises(KeyError) as ctx:
            start_new(deps)
        self.assertIn(bad_key, str(ctx.exception))

    def test_start_new_successful_flow(self):
        parsed_mock_data = {uuid.uuid4().hex: random.randint(1, 1000)}
        sentiment_mock_result = {uuid.uuid4().hex: uuid.uuid4().hex}
        optimizer_expected_result = {uuid.uuid4().hex: random.random()}

        deps = {k: MagicMock() for k in self.required_keys}
        deps["market_parser"].parse.return_value = parsed_mock_data
        deps["market_news_sentiment_analyzer"].analyze.return_value = sentiment_mock_result
        deps["market_portfolio_strategy_optimizer"].optimize.return_value = optimizer_expected_result

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200

            res = start_new(deps)

            deps["market_parser"].parse.assert_called_once()
            deps["market_news_sentiment_analyzer"].analyze.assert_called_once_with(parsed_mock_data)
            deps["market_anomaly_detector"].detect.assert_called_once_with(parsed_mock_data)
            mock_get.assert_called_once()

            called_args, called_kwargs = deps["market_portfolio_strategy_optimizer"].optimize.call_args
            self.assertEqual(called_args[0]["sentiment"], sentiment_mock_result)
            self.assertEqual(called_args[0]["parsed"], parsed_mock_data)
            self.assertEqual(res, optimizer_expected_result)

    def test_market_portfolio_rebalance_engine_execute(self):
        engine = MarketPortfolioRebalanceEngine()
        portfolio_id = uuid.uuid4().hex
        job_id = uuid.uuid4().hex

        mock_portfolio = {
            "portfolio_id": portfolio_id,
            "assets": {"ETH": random.uniform(1.0, 10.0)}
        }

        with patch("skills.market_portfolio_rebalance_engine.db_storage") as mock_db, \
             patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file:

            mock_db.get_portfolio.return_value = mock_portfolio

            config = {
                "portfolio_id": portfolio_id,
                "job_id": job_id
            }

            result = engine.execute_rebalance(config)

            mock_db.get_portfolio.assert_called_once_with(portfolio_id)
            mock_db.save_portfolio.assert_called_once()
            mock_makedirs.assert_called_once()
            mock_file.assert_called_once()

            self.assertEqual(result["status"], "SUCCESS")
            self.assertEqual(result["job_id"], job_id)
            self.assertIn("executed_trades", result)


if __name__ == "__main__":
    unittest.main()