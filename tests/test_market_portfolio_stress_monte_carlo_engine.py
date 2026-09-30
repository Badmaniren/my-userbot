import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.market_portfolio_stress_monte_carlo_engine import start_new


class TestMarketPortfolioStressMonteCarloEngine(unittest.TestCase):

    def setUp(self):
        self.dependencies = {
            f"dep_{uuid.uuid4().hex[:6]}": MagicMock()
            for _ in range(52)
        }
        self.valid_keys = [
            "db_storage", "extractor_tool_1790087207", "extractor_tool_1790102839",
            "extractor_tool_1790262909", "extractor_tool_1790621808", "market_anomaly_detector",
            "market_insider_activity_tracker", "market_insider_alert_pipeline",
            "market_insider_anomaly_analyzer", "market_insider_anomaly_report_bridge",
            "market_news_sentiment_analyzer", "market_parser", "market_portfolio_alert_dispatcher",
            "market_portfolio_alert_event_sink", "market_portfolio_alert_filter_router",
            "market_portfolio_api_gateway", "market_portfolio_audit_alert_notifier",
            "market_portfolio_audit_compliance_hub", "market_portfolio_audit_log_exporter",
            "market_portfolio_autonomous_sentinel", "market_portfolio_backtest_evaluator_bridge",
            "market_portfolio_backtester", "market_portfolio_collector_agent",
            "market_portfolio_data_exporter", "market_portfolio_digest",
            "market_portfolio_dividend_tracker", "market_portfolio_event_intelligence_hub",
            "market_portfolio_execution_pipeline", "market_portfolio_integration_hub",
            "market_portfolio_monitor", "market_portfolio_performance_analytics",
            "market_portfolio_predictive_aggregator", "market_portfolio_scenario_simulator",
            "market_portfolio_slippage_model", "market_portfolio_strategy_optimizer",
            "market_portfolio_stress_recovery_coordinator_bridge", "market_portfolio_stress_reporter",
            "market_portfolio_stress_scenario_pipeline", "market_portfolio_tax_calculator",
            "market_portfolio_telegram_command_center", "market_portfolio_telegram_notifier",
            "market_portfolio_valuation", "market_portfolio_visualizer_v2",
            "market_portfolio_webhook_event_logger", "market_portfolio_webhook_sync",
            "market_report_generator", "market_sentiment_digest",
            "market_sentiment_risk_alert_bridge", "market_sentiment_risk_hub",
            "market_sentiment_telegram_publisher", "market_telegram_pipeline"
        ]

    def test_start_new_success_flow(self):
        complete_payload = {key: MagicMock() for key in self.valid_keys}
        rand_sim_id = uuid.uuid4().hex
        rand_iterations = random.randint(100, 10000)

        complete_payload["market_portfolio_scenario_simulator"].run_simulation.return_value = {
            "simulation_id": rand_sim_id,
            "iterations": rand_iterations,
            "status": "completed"
        }

        with patch("skills.market_portfolio_stress_monte_carlo_engine.uuid4", return_value=uuid.UUID(rand_sim_id)):
            result = start_new(complete_payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("simulation_id"), rand_sim_id)
        self.assertEqual(result.get("iterations"), rand_iterations)
        complete_payload["market_portfolio_scenario_simulator"].run_simulation.assert_called_once()

    def test_start_new_missing_dependency_raises(self):
        incomplete_payload = {key: MagicMock() for key in self.valid_keys[:25]}

        with self.assertRaises((KeyError, ValueError, TypeError)):
            start_new(incomplete_payload)

    def test_start_new_io_stream_handling(self):
        complete_payload = {key: MagicMock() for key in self.valid_keys}
        random_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=64)).encode("utf-8")
        mock_stream = io.BytesIO(random_bytes)

        complete_payload["market_portfolio_data_exporter"].export_stream.return_value = mock_stream

        with patch("skills.market_portfolio_stress_monte_carlo_engine.io.BytesIO", return_value=mock_stream):
            result = start_new(complete_payload)

        self.assertIsNotNone(result)
        complete_payload["market_portfolio_data_exporter"].export_stream.assert_called()

    def test_start_new_anomaly_integration(self):
        complete_payload = {key: MagicMock() for key in self.valid_keys}
        anomaly_score = random.uniform(0.01, 0.99)
        complete_payload["market_anomaly_detector"].evaluate_risk.return_value = {"anomaly_score": anomaly_score}

        result = start_new(complete_payload)

        self.assertIsInstance(result, dict)
        complete_payload["market_anomaly_detector"].evaluate_risk.assert_called_once()


if __name__ == "__main__":
    unittest.main()