import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.market_portfolio_stress_audit_risk_telemetry import start_new


class TestMarketPortfolioStressAuditRiskTelemetry(unittest.TestCase):

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
            "market_portfolio_stress_audit_exporter_v2": MagicMock(),
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
            "market_portfolio_valuation": "...",
            "market_portfolio_var_liquidity_core": "...",
            "market_portfolio_visualizer_v2": "...",
            "market_portfolio_webhook_event_logger": "...",
            "market_portfolio_webhook_sync": "...",
            "market_report_generator": "...",
            "market_sentiment_digest": "...",
            "market_sentiment_risk_alert_bridge": "...",
            "market_sentiment_risk_hub": "...",
            "market_sentiment_telegram_publisher": "...",
            "market_telegram_pipeline": "..."
        }

    def test_start_new_telemetry_collection_success(self):
        expected_telemetry_id = uuid.uuid4().hex
        random_metric_value = random.uniform(10.5, 999.99)
        random_stream_data = io.BytesIO(uuid.uuid4().bytes + random.choice(string.ascii_letters).encode('utf-8'))

        self.dependencies["market_portfolio_collector_agent"].collect.return_value = {
            "telemetry_id": expected_telemetry_id,
            "metric": random_metric_value
        }

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok", "id": expected_telemetry_id}
            mock_post.return_value = mock_response

            result = start_new(self.dependencies, telemetry_stream=random_stream_data)

            self.assertIsNotNone(result)
            self.assertEqual(result.get("telemetry_id"), expected_telemetry_id)
            self.assertEqual(result.get("metric"), random_metric_value)
            mock_post.assert_called_once()

    def test_start_new_telemetry_failure_handling(self):
        random_error_code = random.randint(500, 599)
        random_error_msg = uuid.uuid4().hex
        random_stream_data = io.BytesIO(uuid.uuid4().bytes)

        self.dependencies["market_portfolio_collector_agent"].collect.side_effect = Exception(random_error_msg)

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = random_error_code
            mock_post.return_value = mock_response

            with self.assertRaises(Exception) as context:
                start_new(self.dependencies, telemetry_stream=random_stream_data)

            self.assertIn(random_error_msg, str(context.exception))

    def test_start_new_data_export_integration(self):
        random_batch_id = uuid.uuid4().hex
        random_stream_data = io.BytesIO(uuid.uuid4().bytes)

        exporter_mock = self.dependencies["market_portfolio_stress_audit_exporter_v2"]
        exporter_mock.export.return_value = {"batch_id": random_batch_id, "exported": True}

        result = start_new(self.dependencies, telemetry_stream=random_stream_data)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("batch_id"), random_batch_id)
        self.assertTrue(result.get("exported"))
        exporter_mock.export.assert_called_once()