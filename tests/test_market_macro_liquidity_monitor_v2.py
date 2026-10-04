import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_macro_liquidity_monitor_v2 import start_new


class TestMarketMacroLiquidityMonitorV2(unittest.TestCase):

    def setUp(self):
        self.random_hex = uuid.uuid4().hex
        self.random_string = ''.join(random.choices(string.ascii_letters, k=12))
        self.random_int = random.randint(100, 99999)
        self.random_float = random.uniform(1.0, 1000.0)
        self.random_url = f"https://{self.random_string}.com/{uuid.uuid4().hex}"

        self.mock_db_storage = MagicMock()
        self.mock_extractor_1 = MagicMock()
        self.mock_extractor_2 = MagicMock()
        self.mock_extractor_3 = MagicMock()
        self.mock_extractor_4 = MagicMock()
        self.mock_anomaly_detector = MagicMock()
        self.mock_insider_tracker = MagicMock()
        self.mock_alert_pipeline = MagicMock()

    def test_start_new_successful_execution(self):
        expected_metric_key = f"metric_{self.random_hex}"
        expected_value = self.random_float

        self.mock_db_storage.fetch_liquidity_data.return_value = {
            expected_metric_key: expected_value
        }
        self.mock_extractor_1.extract.return_value = io.BytesIO(self.random_string.encode('utf-8'))

        with patch('skills.market_macro_liquidity_monitor_v2.db_storage', self.mock_db_storage), \
             patch('skills.market_macro_liquidity_monitor_v2.extractor_tool_1790087207', self.mock_extractor_1):

            result = start_new(
                db_storage=self.mock_db_storage,
                extractor_tool_1790087207=self.mock_extractor_1,
                extractor_tool_1790102839=self.mock_extractor_2,
                extractor_tool_1790262909=self.mock_extractor_3,
                extractor_tool_1790621808=self.mock_extractor_4,
                market_anomaly_detector=self.mock_anomaly_detector,
                market_insider_activity_tracker=self.mock_insider_tracker,
                market_insider_alert_pipeline=self.mock_alert_pipeline,
                market_insider_anomaly_analyzer=MagicMock(),
                market_insider_anomaly_report_bridge=MagicMock(),
                market_news_sentiment_analyzer=MagicMock(),
                market_parser=MagicMock(),
                market_portfolio_alert_dispatcher=MagicMock(),
                market_portfolio_alert_event_sink=MagicMock(),
                market_portfolio_alert_filter_router=MagicMock(),
                market_portfolio_api_gateway=MagicMock(),
                market_portfolio_audit_alert_notifier=MagicMock(),
                market_portfolio_audit_compliance_hub=MagicMock(),
                market_portfolio_audit_log_exporter=MagicMock(),
                market_portfolio_autonomous_sentinel=MagicMock(),
                market_portfolio_backtest_evaluator_bridge=MagicMock(),
                market_portfolio_backtester=MagicMock(),
                market_portfolio_collector_agent=MagicMock(),
                market_portfolio_data_exporter=MagicMock(),
                market_portfolio_digest=MagicMock(),
                market_portfolio_dividend_tracker=MagicMock(),
                market_portfolio_event_intelligence_hub=MagicMock(),
                market_portfolio_execution_cost_optimizer=MagicMock(),
                market_portfolio_execution_pipeline=MagicMock(),
                market_portfolio_integration_hub=MagicMock(),
                market_portfolio_liquidity_scenario_analyzer=MagicMock(),
                market_portfolio_monitor=MagicMock(),
                market_portfolio_performance_analytics=MagicMock(),
                market_portfolio_predictive_aggregator=MagicMock(),
                market_portfolio_scenario_simulator=MagicMock(),
                market_portfolio_slippage_model=MagicMock(),
                market_portfolio_strategy_optimizer=MagicMock(),
                market_portfolio_stress_audit_visualizer=MagicMock(),
                market_portfolio_stress_auto_rebalance_trigger=MagicMock(),
                market_portfolio_stress_monte_carlo_engine=MagicMock(),
                market_portfolio_stress_recovery_coordinator_bridge=MagicMock(),
                market_portfolio_stress_reporter=MagicMock(),
                market_portfolio_stress_scenario_pipeline=MagicMock(),
                market_portfolio_tax_calculator=MagicMock(),
                market_portfolio_telegram_command_center=MagicMock(),
                market_portfolio_telegram_notifier=MagicMock(),
                market_portfolio_valuation=MagicMock(),
                market_portfolio_var_liquidity_core=MagicMock(),
                market_portfolio_visualizer_v2=MagicMock(),
                market_portfolio_webhook_event_logger=MagicMock(),
                market_portfolio_webhook_sync=MagicMock(),
                market_report_generator=MagicMock(),
                market_sentiment_digest=MagicMock(),
                market_sentiment_risk_alert_bridge=MagicMock(),
                market_sentiment_risk_hub=MagicMock(),
                market_sentiment_telegram_publisher=MagicMock(),
                market_telegram_pipeline=MagicMock()
            )

            self.assertIsNotNone(result)
            self.assertIn(expected_metric_key, str(result))

    def test_start_new_handles_extraction_error(self):
        error_message = f"err_{self.random_hex}"
        self.mock_extractor_1.extract.side_effect = Exception(error_message)

        with patch('skills.market_macro_liquidity_monitor_v2.extractor_tool_1790087207', self.mock_extractor_1):
            try:
                start_new(
                    db_storage=self.mock_db_storage,
                    extractor_tool_1790087207=self.mock_extractor_1,
                    extractor_tool_1790102839=self.mock_extractor_2,
                    extractor_tool_1790262909=self.mock_extractor_3,
                    extractor_tool_1790621808=self.mock_extractor_4,
                    market_anomaly_detector=self.mock_anomaly_detector,
                    market_insider_activity_tracker=self.mock_insider_tracker,
                    market_insider_alert_pipeline=self.mock_alert_pipeline,
                    market_insider_anomaly_analyzer=MagicMock(),
                    market_insider_anomaly_report_bridge=MagicMock(),
                    market_news_sentiment_analyzer=MagicMock(),
                    market_parser=MagicMock(),
                    market_portfolio_alert_dispatcher=MagicMock(),
                    market_portfolio_alert_event_sink=MagicMock(),
                    market_portfolio_alert_filter_router=MagicMock(),
                    market_portfolio_api_gateway=MagicMock(),
                    market_portfolio_audit_alert_notifier=MagicMock(),
                    market_portfolio_audit_compliance_hub=MagicMock(),
                    market_portfolio_audit_log_exporter=MagicMock(),
                    market_portfolio_autonomous_sentinel=MagicMock(),
                    market_portfolio_backtest_evaluator_bridge=MagicMock(),
                    market_portfolio_backtester=MagicMock(),
                    market_portfolio_collector_agent=MagicMock(),
                    market_portfolio_data_exporter=MagicMock(),
                    market_portfolio_digest=MagicMock(),
                    market_portfolio_dividend_tracker=MagicMock(),
                    market_portfolio_event_intelligence_hub=MagicMock(),
                    market_portfolio_execution_cost_optimizer=MagicMock(),
                    market_portfolio_execution_pipeline=MagicMock(),
                    market_portfolio_integration_hub=MagicMock(),
                    market_portfolio_liquidity_scenario_analyzer=MagicMock(),
                    market_portfolio_monitor=MagicMock(),
                    market_portfolio_performance_analytics=MagicMock(),
                    market_portfolio_predictive_aggregator=MagicMock(),
                    market_portfolio_scenario_simulator=MagicMock(),
                    market_portfolio_slippage_model=MagicMock(),
                    market_portfolio_strategy_optimizer=MagicMock(),
                    market_portfolio_stress_audit_visualizer=MagicMock(),
                    market_portfolio_stress_auto_rebalance_trigger=MagicMock(),
                    market_portfolio_stress_monte_carlo_engine=MagicMock(),
                    market_portfolio_stress_recovery_coordinator_bridge=MagicMock(),
                    market_portfolio_stress_reporter=MagicMock(),
                    market_portfolio_stress_scenario_pipeline=MagicMock(),
                    market_portfolio_tax_calculator=MagicMock(),
                    market_portfolio_telegram_command_center=MagicMock(),
                    market_portfolio_telegram_notifier=MagicMock(),
                    market_portfolio_valuation=MagicMock(),
                    market_portfolio_var_liquidity_core=MagicMock(),
                    market_portfolio_visualizer_v2=MagicMock(),
                    market_portfolio_webhook_event_logger=MagicMock(),
                    market_portfolio_webhook_sync=MagicMock(),
                    market_report_generator=MagicMock(),
                    market_sentiment_digest=MagicMock(),
                    market_sentiment_risk_alert_bridge=MagicMock(),
                    market_sentiment_risk_hub=MagicMock(),
                    market_sentiment_telegram_publisher=MagicMock(),
                    market_telegram_pipeline=MagicMock()
                )
            except Exception as e:
                self.assertIn(error_message, str(e))

    def test_start_new_anomaly_trigger(self):
        anomaly_payload = f"anomaly_{self.random_hex}"
        self.mock_anomaly_detector.check_liquidity.return_value = {
            "status": "critical",
            "payload": anomaly_payload
        }

        with patch('skills.market_macro_liquidity_monitor_v2.market_anomaly_detector', self.mock_anomaly_detector):
            result = start_new(
                db_storage=self.mock_db_storage,
                extractor_tool_1790087207=self.mock_extractor_1,
                extractor_tool_1790102839=self.mock_extractor_2,
                extractor_tool_1790262909=self.mock_extractor_3,
                extractor_tool_1790621808=self.mock_extractor_4,
                market_anomaly_detector=self.mock_anomaly_detector,
                market_insider_activity_tracker=self.mock_insider_tracker,
                market_insider_alert_pipeline=self.mock_alert_pipeline,
                market_insider_anomaly_analyzer=MagicMock(),
                market_insider_anomaly_report_bridge=MagicMock(),
                market_news_sentiment_analyzer=MagicMock(),
                market_parser=MagicMock(),
                market_portfolio_alert_dispatcher=MagicMock(),
                market_portfolio_alert_event_sink=MagicMock(),
                market_portfolio_alert_filter_router=MagicMock(),
                market_portfolio_api_gateway=MagicMock(),
                market_portfolio_audit_alert_notifier=MagicMock(),
                market_portfolio_audit_compliance_hub=MagicMock(),
                market_portfolio_audit_log_exporter=MagicMock(),
                market_portfolio_autonomous_sentinel=MagicMock(),
                market_portfolio_backtest_evaluator_bridge=MagicMock(),
                market_portfolio_backtester=MagicMock(),
                market_portfolio_collector_agent=MagicMock(),
                market_portfolio_data_exporter=MagicMock(),
                market_portfolio_digest=MagicMock(),
                market_portfolio_dividend_tracker=MagicMock(),
                market_portfolio_event_intelligence_hub=MagicMock(),
                market_portfolio_execution_cost_optimizer=MagicMock(),
                market_portfolio_execution_pipeline=MagicMock(),
                market_portfolio_integration_hub=MagicMock(),
                market_portfolio_liquidity_scenario_analyzer=MagicMock(),
                market_portfolio_monitor=MagicMock(),
                market_portfolio_performance_analytics=MagicMock(),
                market_portfolio_predictive_aggregator=MagicMock(),
                market_portfolio_scenario_simulator=MagicMock(),
                market_portfolio_slippage_model=MagicMock(),
                market_portfolio_strategy_optimizer=MagicMock(),
                market_portfolio_stress_audit_visualizer=MagicMock(),
                market_portfolio_stress_auto_rebalance_trigger=MagicMock(),
                market_portfolio_stress_monte_carlo_engine=MagicMock(),
                market_portfolio_stress_recovery_coordinator_bridge=MagicMock(),
                market_portfolio_stress_reporter=MagicMock(),
                market_portfolio_stress_scenario_pipeline=MagicMock(),
                market_portfolio_tax_calculator=MagicMock(),
                market_portfolio_telegram_command_center=MagicMock(),
                market_portfolio_telegram_notifier=MagicMock(),
                market_portfolio_valuation=MagicMock(),
                market_portfolio_var_liquidity_core=MagicMock(),
                market_portfolio_visualizer_v2=MagicMock(),
                market_portfolio_webhook_event_logger=MagicMock(),
                market_portfolio_webhook_sync=MagicMock(),
                market_report_generator=MagicMock(),
                market_sentiment_digest=MagicMock(),
                market_sentiment_risk_alert_bridge=MagicMock(),
                market_sentiment_risk_hub=MagicMock(),
                market_sentiment_telegram_publisher=MagicMock(),
                market_telegram_pipeline=MagicMock()
            )

            self.assertIsNotNone(result)
            self.assertTrue(self.mock_anomaly_detector.check_liquidity.called)