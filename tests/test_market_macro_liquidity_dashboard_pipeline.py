import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.market_macro_liquidity_dashboard_pipeline import start_new

class TestMarketMacroLiquidityDashboardPipeline(unittest.TestCase):
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
            "market_portfolio_var_liquidity_core": "...",
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

    def test_start_new_success_pipeline_execution(self):
        rand_macro_id = uuid.uuid4().hex
        rand_liquidity_val = random.uniform(1000.0, 99999.9)
        rand_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))

        self.dependencies["extractor_tool_1790087207"].fetch_macro_data.return_value = {
            'id': rand_macro_id,
            'metric': rand_metric_name
        }
        self.dependencies["market_portfolio_var_liquidity_core"] = rand_liquidity_val

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = io.BytesIO(uuid.uuid4().bytes).read()
            mock_get.return_value = mock_response

            result = start_new(**self.dependencies)

            self.assertIsNotNone(result)
            self.assertTrue(isinstance(result, (dict, list, str, int, bool)))
            self.dependencies["extractor_tool_1790087207"].fetch_macro_data.assert_called_once()

    def test_start_new_anomaly_trigger(self):
        rand_anomaly_code = uuid.uuid4().hex[:8]
        self.dependencies["market_anomaly_detector"].check_anomaly.return_value = {
            'status': 'CRITICAL',
            'code': rand_anomaly_code
        }

        with patch('uuid.uuid4', return_value=uuid.UUID(int=random.getrandbits(128))):
            try:
                res = start_new(**self.dependencies)
            except Exception as e:
                self.fail(f"Pipeline crashed on anomaly trigger: {e}")

        self.dependencies["market_anomaly_detector"].check_anomaly.assert_called()

    def test_start_new_empty_stream_handling(self):
        stream_data = io.BytesIO(b'')
        self.dependencies["market_parser"].parse_stream.return_value = stream_data

        try:
            res = start_new(**self.dependencies)
        except Exception as e:
            self.fail(f"Pipeline failed to handle empty stream safely: {e}")

        self.dependencies["market_parser"].parse_stream.assert_called_once()

    def test_start_new_db_storage_integration(self):
        rand_key = uuid.uuid4().hex
        rand_val = random.randint(1, 100000)

        mock_db = self.dependencies["db_storage"]
        mock_db.retrieve.return_value = {rand_key: rand_val}

        result = start_new(**self.dependencies)
        mock_db.retrieve.assert_called()

    def test_start_new_exception_resilience(self):
        self.dependencies["market_portfolio_monitor"].track.side_effect = RuntimeError(uuid.uuid4().hex)

        with self.assertRaises(Exception):
            start_new(**self.dependencies)