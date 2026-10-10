import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.market_portfolio_stress_auto_hedge_engine import start_new


class TestMarketPortfolioStressAutoHedgeEngine(unittest.TestCase):

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
            "market_portfolio_liquidity_scenario_analyzer": MagicMock(),
            "market_portfolio_monitor": MagicMock(),
            "market_portfolio_performance_analytics": MagicMock(),
            "market_portfolio_predictive_aggregator": MagicMock(),
            "market_portfolio_scenario_simulator": MagicMock(),
            "market_portfolio_slippage_model": MagicMock(),
            "market_portfolio_strategy_optimizer": MagicMock(),
            "market_portfolio_stress_alert_dashboard_bridge": MagicMock(),
            "market_portfolio_stress_alert_emitter": MagicMock(),
            "market_portfolio_stress_audit_exporter_v2": MagicMock(),
            "market_portfolio_stress_audit_realtime_streamer": MagicMock(),
            "market_portfolio_stress_audit_scheduler_hub": MagicMock(),
            "market_portfolio_stress_audit_summary_vault": MagicMock(),
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
            "market_sentiment_telegram_publisher": "...",
            "market_telegram_pipeline": "..."
        }

    def test_start_new_initialization_and_execution(self):
        rand_scenario_id = uuid.uuid4().hex
        rand_threshold = random.uniform(0.01, 0.99)
        rand_payload = "".join(random.choices(string.ascii_letters + string.digits, k=32))

        self.dependencies["market_portfolio_scenario_simulator"].simulate.return_value = {
            "scenario_id": rand_scenario_id,
            "failure_detected": True,
            "risk_score": rand_threshold
        }

        stream_data = io.BytesIO(rand_payload.encode('utf-8'))

        with patch("skills.market_portfolio_stress_auto_hedge_engine.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raw = stream_data
            mock_response.text = rand_payload
            mock_get.return_value = mock_response

            result = start_new(self.dependencies)

            self.assertIsNotNone(result)
            self.dependencies["market_portfolio_scenario_simulator"].simulate.assert_called()
            self.dependencies["db_storage"].save.assert_called()

    def test_start_new_handles_stress_failure_and_hedging(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_loss_limit = random.randint(1000, 500000)

        self.dependencies["market_portfolio_monitor"].get_active_portfolio.return_value = {
            "portfolio_id": rand_portfolio_id,
            "max_tolerable_loss": rand_loss_limit
        }

        with patch("skills.market_portfolio_stress_auto_hedge_engine.uuid.uuid4") as mock_uuid:
            generated_hedge_id = uuid.uuid4()
            mock_uuid.return_value = generated_hedge_id

            result = start_new(self.dependencies)

            self.assertIsInstance(result, dict)
            self.assertIn("hedge_id", result)
            self.assertEqual(result["hedge_id"], generated_hedge_id)
            self.dependencies["market_portfolio_execution_pipeline"].execute.assert_called()

    def test_start_new_with_malformed_stream_and_recovery(self):
        rand_garbage = bytes([random.randint(0, 255) for _ in range(64)])
        garbage_stream = io.BytesIO(rand_garbage)

        self.dependencies["market_portfolio_stress_monte_carlo_engine"].run_simulation.side_effect = Exception("Monte Carlo Collapse")

        with patch("skills.market_portfolio_stress_auto_hedge_engine.sys.stdin", garbage_stream):
            try:
                res = start_new(self.dependencies)
            except Exception:
                res = None

            self.assertTrue(res is None or isinstance(res, dict))
            self.dependencies["market_portfolio_stress_recovery_coordinator_bridge"].handle_failure.assert_called()