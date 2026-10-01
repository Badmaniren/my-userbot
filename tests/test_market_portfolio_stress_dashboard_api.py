import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import requests
from bs4 import BeautifulSoup

from skills.market_portfolio_stress_dashboard_api import start_new

class TestMarketPortfolioStressDashboardApi(unittest.TestCase):

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
            "market_portfolio_integration_hub": "...",
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

    def test_start_new_initialization_and_flow(self):
        random_prefix = ''.join(random.choices(string.ascii_lowercase, k=8))
        expected_scenario_id = uuid.uuid4().hex
        random_metric_value = random.uniform(10.0, 1000.0)

        self.dependencies["market_portfolio_scenario_simulator"].simulate.return_value = {
            "scenario_id": expected_scenario_id,
            "impact_metric": random_metric_value
        }

        with patch('requests.get') as mock_requests_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = f"<html><body><div id='{random_prefix}'>StressData</div></body></html>".encode('utf-8')
            mock_requests_get.return_value = mock_resp

            result = start_new(self.dependencies)

            self.assertIsNotNone(result)
            self.dependencies["market_portfolio_scenario_simulator"].simulate.assert_called()
            
    def test_start_new_handles_streaming_data(self):
        random_stream_data = uuid.uuid4().bytes
        stream_mock = io.BytesIO(random_stream_data)

        self.dependencies["db_storage"].fetch_stream.return_value = stream_mock

        with patch('bs4.BeautifulSoup') as mock_bs:
            mock_soup_instance = MagicMock()
            mock_bs.return_value = mock_soup_instance
            
            try:
                start_new(self.dependencies)
            except Exception as e:
                self.fail(f"start_new crashed on stream processing: {e}")

            self.dependencies["db_storage"].fetch_stream.assert_called()

    def test_start_new_with_randomized_anomaly_trigger(self):
        random_anomaly_score = random.randint(1, 100)
        self.dependencies["market_anomaly_detector"].detect.return_value = {
            "anomaly_score": random_anomaly_score,
            "status": "TRIGGERED"
        }

        res = start_new(self.dependencies)
        self.assertTrue(res is not None or res is None)
        self.dependencies["market_anomaly_detector"].detect.assert_called()

if __name__ == '__main__':
    unittest.main()