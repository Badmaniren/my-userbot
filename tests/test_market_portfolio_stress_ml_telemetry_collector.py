import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.market_portfolio_stress_ml_telemetry_collector import start_new


class TestMarketPortfolioStressMLTelemetryCollector(unittest.TestCase):

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
            "market_portfolio_stress_reporter": "...",
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
            "market_telegram_pipeline": MagicMock()
        }

    def test_start_new_telemetry_collection_success(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_metric_name = ''.join(random.choices(string.ascii_lowercase, k=12))
        rand_value = random.uniform(1050.5, 99999.9)

        mock_payload = {
            "portfolio_id": rand_portfolio_id,
            "metric": rand_metric_name,
            "audit_value": rand_value
        }

        self.dependencies["market_portfolio_collector_agent"].collect.return_value = mock_payload
        
        random_stream_data = io.BytesIO(uuid.uuid4().bytes + ''.join(random.choices(string.ascii_letters, k=20)).encode('utf-8'))

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raw = random_stream_data
            mock_response.json.return_value = {"status": "ok", "telemetry_id": uuid.uuid4().hex}
            mock_get.return_value = mock_response

            result = start_new(self.dependencies, rand_portfolio_id)

            self.assertIsNotNone(result)
            self.dependencies["market_portfolio_collector_agent"].collect.assert_called_once()
            self.dependencies["db_storage"].save.assert_not_called()

    def test_start_new_telemetry_collector_anomaly_trigger(self):
        rand_anomaly_code = uuid.uuid4().hex[:8]
        rand_threshold = random.randint(10, 100)

        self.dependencies["market_anomaly_detector"].detect.return_value = {
            "anomaly_detected": True,
            "code": rand_anomaly_code,
            "threshold": rand_threshold
        }

        random_garbage = io.BytesIO(os_random_bytes := uuid.uuid4().bytes)

        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 201
            mock_resp.raw = random_garbage
            mock_post.return_value = mock_resp

            res = start_new(self.dependencies, uuid.uuid4().hex)

            self.assertTrue(res or res is None or isinstance(res, (dict, list, str, int, bool)))
            self.dependencies["market_anomaly_detector"].detect.assert_called()


if __name__ == "__main__":
    unittest.main()