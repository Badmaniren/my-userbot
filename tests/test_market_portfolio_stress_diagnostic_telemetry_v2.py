import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_stress_diagnostic_telemetry_v2 import start_new

target_patch = "tests.test_market_portfolio_stress_diagnostic_telemetry_v2.start_new"


class TestMarketPortfolioStressDiagnosticTelemetryV2(unittest.TestCase):
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

    def test_start_new_execution_with_chaos_inputs(self):
        random_key = uuid.uuid4().hex
        random_val = random.randint(1000, 99999)

        with patch(target_patch, return_value={random_key: random_val}) as mock_start:
            stream_data = io.BytesIO(uuid.uuid4().bytes)
            res = start_new(stream_data, **self.dependencies)
            self.assertIn(random_key, res)
            self.assertEqual(res[random_key], random_val)

    def test_start_new_with_randomized_payloads(self):
        payload_id = uuid.uuid4().hex
        expected_metric = random.uniform(0.01, 999.99)

        with patch(target_patch) as mock_start:
            mock_start.return_value = {payload_id: expected_metric}

            result = start_new(
                telemetry_token=uuid.uuid4().hex,
                payload_size=random.randint(10, 500),
                **self.dependencies
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result[payload_id], expected_metric)

    def test_start_new_stream_handling(self):
        trash_stream = io.BytesIO("".join(random.choices(string.ascii_letters, k=64)).encode('utf-8'))
        dynamic_key = uuid.uuid4().hex

        with patch(target_patch, return_value={dynamic_key: trash_stream.getvalue()}) as mock_start:
            output = start_new(stream=trash_stream, **self.dependencies)
            self.assertIn(dynamic_key, output)
            self.assertEqual(output[dynamic_key], trash_stream.getvalue())

    def test_start_new_direct_bytes_stream(self):
        stream_data = io.BytesIO(b"hello telemetry")
        res = start_new(stream_data)
        self.assertIsInstance(res, dict)
        self.assertEqual(len(res), 1)
        key = list(res.keys())[0]
        self.assertEqual(res[key], "hello telemetry")

    def test_start_new_direct_str_stream(self):
        stream_data = io.StringIO("string telemetry stream")
        res = start_new(stream=stream_data)
        self.assertIsInstance(res, dict)
        key = list(res.keys())[0]
        self.assertEqual(res[key], "string telemetry stream")

    def test_start_new_direct_kwargs(self):
        res = start_new(payload_size=256)
        self.assertIsInstance(res, dict)
        key = list(res.keys())[0]
        self.assertEqual(res[key], 256)


if __name__ == '__main__':
    unittest.main()
