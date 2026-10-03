import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.none import start_new


class TestArchitectInquisitorStartNew(unittest.TestCase):

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
            "market_sentiment_risk_alert_bridge": "...",
            "market_sentiment_risk_hub": "...",
            "market_sentiment_telegram_publisher": "...",
            "market_telegram_pipeline": "..."
        }

    def test_start_new_execution_flow(self):
        random_seed_val = random.randint(1000, 99999)
        random_token = uuid.uuid4().hex
        random_payload = ''.join(random.choices(string.ascii_letters + string.digits, k=64))

        stream_mock = io.BytesIO(random_payload.encode('utf-8'))

        with patch('skills.none.requests.get') as mock_req_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "seed": random_seed_val,
                "token": random_token,
                "payload": random_payload
            }
            mock_req_get.return_value = mock_response

            result = start_new(**self.dependencies)

            mock_req_get.assert_called_once()
            self.assertIsNotNone(result)

    def test_start_new_handles_anomalies(self):
        random_error_code = random.randint(400, 599)
        random_url = f"https://{uuid.uuid4().hex}.market.internal/api/v2/macro"

        with patch('skills.none.requests.get') as mock_req_get:
            mock_response = MagicMock()
            mock_response.status_code = random_error_code
            mock_response.raise_for_status.side_effect = Exception(f"HTTP Error {random_error_code}")
            mock_req_get.return_value = mock_response

            with self.assertRaises(Exception):
                start_new(**self.dependencies)

    def test_start_new_data_propagation(self):
        expected_metric_id = uuid.uuid4().hex
        random_threshold = random.random() * 100

        self.dependencies["market_anomaly_detector"].evaluate.return_value = {
            "metric_id": expected_metric_id,
            "threshold": random_threshold,
            "status": "INITIALIZED"
        }

        result = start_new(**self.dependencies)

        self.dependencies["market_anomaly_detector"].evaluate.assert_called()

if __name__ == '__main__':
    unittest.main()