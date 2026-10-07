import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_stress_resilience_guard import start_new


class TestMarketPortfolioStressResilienceGuard(unittest.TestCase):

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
            "market_portfolio_digest": string.ascii_letters,
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
            "market_telegram_pipeline": MagicMock(),
        }

    def test_start_new_success_flow(self):
        random_seed_val = random.randint(1000, 99999)
        expected_metric_id = uuid.uuid4().hex
        random_bytes_content = uuid.uuid4().bytes

        self.dependencies["market_portfolio_stress_monte_carlo_engine"].run_simulation.return_value = {
            "metric_id": expected_metric_id,
            "resilience_score": random.uniform(0.0, 100.0)
        }

        with patch("skills.market_portfolio_stress_resilience_guard.io.BytesIO", return_value=io.BytesIO(random_bytes_content)) as mock_bytes_io:
            result = start_new(self.dependencies, seed=random_seed_val)

        self.assertIsNotNone(result)
        self.dependencies["market_portfolio_stress_monte_carlo_engine"].run_simulation.assert_called_once()
        
        if isinstance(result, dict):
            self.assertIn("metric_id", result)
            self.assertEqual(result["metric_id"], expected_metric_id)

    def test_start_new_exception_handling(self):
        random_error_msg = uuid.uuid4().hex
        self.dependencies["market_portfolio_stress_monte_carlo_engine"].run_simulation.side_effect = ValueError(random_error_msg)

        with self.assertRaises(ValueError) as ctx:
            start_new(self.dependencies)

        self.assertIn(random_error_msg, str(ctx.exception))

    def test_start_new_validation_failure(self):
        random_invalid_metric = uuid.uuid4().hex
        self.dependencies["market_portfolio_stress_scenario_pipeline"].evaluate.return_value = {
            "status": "FAILED",
            "reason": random_invalid_metric
        }

        with patch("skills.market_portfolio_stress_resilience_guard.random.choice", return_value=random_invalid_metric):
            try:
                res = start_new(self.dependencies)
                if res is not None and isinstance(res, dict):
                    self.assertNotEqual(res.get("status"), "SUCCESS")
            except Exception as e:
                self.assertIsInstance(e, (ValueError, RuntimeError, TypeError))


if __name__ == "__main__":
    unittest.main()