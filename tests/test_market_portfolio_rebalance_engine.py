import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_rebalance_engine import start_new

class TestMarketPortfolioRebalanceEngine(unittest.TestCase):

    def setUp(self):
        self.dependencies = {
            "db_storage": MagicMock(),
            "extractor_tool_1790087207": MagicMock(),
            "extractor_tool_1790102839": MagicMock(),
            "extractor_tool_1790262909": MagicMock(),
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
            "market_portfolio_event_intelligence_hub": MagicMock(),
            "market_portfolio_integration_hub": MagicMock(),
            "market_portfolio_monitor": MagicMock(),
            "market_portfolio_performance_analytics": MagicMock(),
            "market_portfolio_predictive_aggregator": MagicMock(),
            "market_portfolio_scenario_simulator": MagicMock(),
            "market_portfolio_strategy_optimizer": MagicMock(),
            "market_portfolio_stress_reporter": MagicMock(),
            "market_portfolio_stress_scenario_pipeline": MagicMock(),
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

    def test_start_new_success_flow(self):
        rand_metric_id = uuid.uuid4().hex
        rand_sentiment_score = random.uniform(-1.0, 1.0)
        rand_payload = ''.join(random.choices(string.ascii_letters + string.digits, k=32))

        self.dependencies["market_parser"].parse.return_value = {
            "metric_id": rand_metric_id,
            "sentiment": rand_sentiment_score
        }
        self.dependencies["market_news_sentiment_analyzer"].analyze.return_value = rand_sentiment_score
        self.dependencies["market_portfolio_strategy_optimizer"].optimize.return_value = {
            "action": "REBALANCE",
            "payload": rand_payload
        }

        with patch("skills.market_portfolio_rebalance_engine.uuid.uuid4", return_value=uuid.UUID(int=random.randint(0, 2**128 - 1))):
            result = start_new(self.dependencies)

        self.assertIsInstance(result, dict)
        self.dependencies["market_parser"].parse.assert_called_once()
        self.dependencies["market_portfolio_strategy_optimizer"].optimize.assert_called_once()
        self.assertIn("action", result)
        self.assertEqual(result["payload"], rand_payload)

    def test_start_new_anomaly_trigger(self):
        rand_anomaly_code = uuid.uuid4().hex[:8]
        rand_stream_data = ''.join(random.choices(string.ascii_letters, k=64)).encode('utf-8')

        self.dependencies["market_anomaly_detector"].detect.return_value = {
            "anomaly_code": rand_anomaly_code,
            "severity": random.choice(["HIGH", "CRITICAL", "MODERATE"])
        }

        mock_stream = io.BytesIO(rand_stream_data)

        with patch("skills.market_portfolio_rebalance_engine.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raw = mock_stream
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            try:
                start_new(self.dependencies)
            except Exception:
                pass

        self.dependencies["market_anomaly_detector"].detect.assert_called()

    def test_start_new_empty_dependencies_raises(self):
        broken_deps = {}
        with self.assertRaises(KeyError):
            start_new(broken_deps)

    def test_start_new_strategy_optimizer_failure(self):
        rand_error_msg = uuid.uuid4().hex
        self.dependencies["market_portfolio_strategy_optimizer"].optimize.side_effect = ValueError(rand_error_msg)

        with self.assertRaises(ValueError) as ctx:
            start_new(self.dependencies)

        self.assertIn(rand_error_msg, str(ctx.exception))

if __name__ == "__main__":
    unittest.main()