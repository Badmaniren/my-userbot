import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
from skills.market_macro_liquidity_monitor import start_new

class TestMarketMacroLiquidityMonitor(unittest.TestCase):

    def setUp(self):
        self.mock_db_storage = MagicMock()
        self.mock_extractor_1 = MagicMock()
        self.mock_extractor_2 = MagicMock()
        self.mock_extractor_3 = MagicMock()
        self.mock_extractor_4 = MagicMock()
        self.mock_anomaly_detector = MagicMock()
        self.mock_insider_tracker = MagicMock()
        self.mock_alert_pipeline = MagicMock()
        self.mock_anomaly_analyzer = MagicMock()
        self.mock_report_bridge = MagicMock()
        self.mock_news_analyzer = MagicMock()
        self.mock_market_parser = MagicMock()
        self.mock_portfolio_dispatcher = MagicMock()
        self.mock_event_sink = MagicMock()
        self.mock_filter_router = MagicMock()
        self.mock_api_gateway = MagicMock()
        self.mock_audit_notifier = MagicMock()
        self.mock_compliance_hub = MagicMock()
        self.mock_log_exporter = MagicMock()
        self.mock_autonomous_sentinel = MagicMock()
        self.mock_backtest_evaluator = MagicMock()
        self.mock_backtester = MagicMock()
        self.mock_collector_agent = MagicMock()
        self.mock_data_exporter = MagicMock()
        self.mock_digest = MagicMock()
        self.mock_dividend_tracker = MagicMock()
        self.mock_event_intelligence = MagicMock()
        self.mock_execution_cost_optimizer = MagicMock()
        self.mock_execution_pipeline = MagicMock()
        self.mock_integration_hub = MagicMock()
        self.mock_liquidity_scenario_analyzer = MagicMock()
        self.mock_portfolio_monitor = MagicMock()
        self.mock_performance_analytics = MagicMock()
        self.mock_predictive_aggregator = MagicMock()
        self.mock_scenario_simulator = MagicMock()
        self.mock_slippage_model = MagicMock()
        self.mock_strategy_optimizer = MagicMock()
        self.mock_stress_audit_visualizer = MagicMock()
        self.mock_stress_auto_rebalance_trigger = MagicMock()
        self.mock_stress_monte_carlo_engine = MagicMock()
        self.mock_stress_recovery_coordinator = MagicMock()
        self.mock_stress_reporter = MagicMock()
        self.mock_stress_scenario_pipeline = MagicMock()
        self.mock_tax_calculator = MagicMock()
        self.mock_telegram_command_center = MagicMock()
        self.mock_telegram_notifier = MagicMock()
        self.mock_valuation = MagicMock()
        self.mock_var_liquidity_core = MagicMock()
        self.mock_visualizer_v2 = MagicMock()
        self.mock_webhook_event_logger = MagicMock()
        self.mock_webhook_sync = MagicMock()
        self.mock_report_generator = MagicMock()
        self.mock_sentiment_digest = MagicMock()
        self.mock_sentiment_risk_alert_bridge = MagicMock()
        self.mock_sentiment_risk_hub = MagicMock()
        self.mock_sentiment_telegram_publisher = MagicMock()
        self.mock_telegram_pipeline = MagicMock()

    def test_start_new_liquidity_monitoring_success(self):
        rand_token = uuid.uuid4().hex
        rand_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        rand_val = random.uniform(100.0, 50000.0)

        self.mock_market_parser.fetch_macro_data.return_value = {
            rand_metric_name: rand_val,
            "token": rand_token
        }

        stream_data = io.BytesIO(f"{rand_token}:{rand_val}".encode('utf-8'))

        with patch('requests.get') as mock_req_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raw = stream_data
            mock_response.text = f"{rand_token}:{rand_val}"
            mock_req_get.return_value = mock_response

            result = start_new(
                db_storage=self.mock_db_storage,
                extractor_tool_1790087207=self.mock_extractor_1,
                extractor_tool_1790102839=self.mock_extractor_2,
                extractor_tool_1790262909=self.mock_extractor_3,
                extractor_tool_1790621808=self.mock_extractor_4,
                market_anomaly_detector=self.mock_anomaly_detector,
                market_insider_activity_tracker=self.mock_insider_tracker,
                market_insider_alert_pipeline=self.mock_alert_pipeline,
                market_insider_anomaly_analyzer=self.mock_anomaly_analyzer,
                market_insider_anomaly_report_bridge=self.mock_report_bridge,
                market_news_sentiment_analyzer=self.mock_news_analyzer,
                market_parser=self.mock_market_parser,
                market_portfolio_alert_dispatcher=self.mock_portfolio_dispatcher,
                market_portfolio_alert_event_sink=self.mock_event_sink,
                market_portfolio_alert_filter_router=self.mock_filter_router,
                market_portfolio_api_gateway=self.mock_api_gateway,
                market_portfolio_audit_alert_notifier=self.mock_audit_notifier,
                market_portfolio_audit_compliance_hub=self.mock_compliance_hub,
                market_portfolio_audit_log_exporter=self.mock_log_exporter,
                market_portfolio_autonomous_sentinel=self.mock_autonomous_sentinel,
                market_portfolio_backtest_evaluator_bridge=self.mock_backtest_evaluator,
                market_portfolio_backtester=self.mock_backtester,
                market_portfolio_collector_agent=self.mock_collector_agent,
                market_portfolio_data_exporter=self.mock_data_exporter,
                market_portfolio_digest=self.mock_digest,
                market_portfolio_dividend_tracker=self.mock_dividend_tracker,
                market_portfolio_event_intelligence_hub=self.mock_event_intelligence,
                market_portfolio_execution_cost_optimizer=self.mock_execution_cost_optimizer,
                market_portfolio_execution_pipeline=self.mock_execution_pipeline,
                market_portfolio_integration_hub=self.mock_integration_hub,
                market_portfolio_liquidity_scenario_analyzer=self.mock_liquidity_scenario_analyzer,
                market_portfolio_monitor=self.mock_portfolio_monitor,
                market_portfolio_performance_analytics=self.mock_performance_analytics,
                market_portfolio_predictive_aggregator=self.mock_predictive_aggregator,
                market_portfolio_scenario_simulator=self.mock_scenario_simulator,
                market_portfolio_slippage_model=self.mock_slippage_model,
                market_portfolio_strategy_optimizer=self.mock_strategy_optimizer,
                market_portfolio_stress_audit_visualizer=self.mock_stress_audit_visualizer,
                market_portfolio_stress_auto_rebalance_trigger=self.mock_stress_auto_rebalance_trigger,
                market_portfolio_stress_monte_carlo_engine=self.mock_stress_monte_carlo_engine,
                market_portfolio_stress_recovery_coordinator_bridge=self.mock_stress_recovery_coordinator,
                market_portfolio_stress_reporter=self.mock_stress_reporter,
                market_portfolio_stress_scenario_pipeline=self.mock_stress_scenario_pipeline,
                market_portfolio_tax_calculator=self.mock_tax_calculator,
                market_portfolio_telegram_command_center=self.mock_telegram_command_center,
                market_portfolio_telegram_notifier=self.mock_telegram_notifier,
                market_portfolio_valuation=self.mock_valuation,
                market_portfolio_var_liquidity_core=self.mock_var_liquidity_core,
                market_portfolio_visualizer_v2=self.mock_visualizer_v2,
                market_portfolio_webhook_event_logger=self.mock_webhook_event_logger,
                market_portfolio_webhook_sync=self.mock_webhook_sync,
                market_report_generator=self.mock_report_generator,
                market_sentiment_digest=self.mock_sentiment_digest,
                market_sentiment_risk_alert_bridge=self.mock_sentiment_risk_alert_bridge,
                market_sentiment_risk_hub=self.mock_sentiment_risk_hub,
                market_sentiment_telegram_publisher=self.mock_sentiment_telegram_publisher,
                market_telegram_pipeline=self.mock_telegram_pipeline
            )

        self.assertIsNotNone(result)
        self.mock_db_storage.save_macro_metric.assert_called()

    def test_start_new_liquidity_anomaly_trigger(self):
        rand_anomaly_code = uuid.uuid4().hex
        self.mock_anomaly_detector.detect.return_value = {"anomaly": True, "code": rand_anomaly_code}

        result = start_new(
            db_storage=self.mock_db_storage,
            extractor_tool_1790087207=self.mock_extractor_1,
            extractor_tool_1790102839=self.mock_extractor_2,
            extractor_tool_1790262909=self.mock_extractor_3,
            extractor_tool_1790621808=self.mock_extractor_4,
            market_anomaly_detector=self.mock_anomaly_detector,
            market_insider_activity_tracker=self.mock_insider_tracker,
            market_insider_alert_pipeline=self.mock_alert_pipeline,
            market_insider_anomaly_analyzer=self.mock_anomaly_analyzer,
            market_insider_anomaly_report_bridge=self.mock_report_bridge,
            market_news_sentiment_analyzer=self.mock_news_analyzer,
            market_parser=self.mock_market_parser,
            market_portfolio_alert_dispatcher=self.mock_portfolio_dispatcher,
            market_portfolio_alert_event_sink=self.mock_event_sink,
            market_portfolio_alert_filter_router=self.mock_filter_router,
            market_portfolio_api_gateway=self.mock_api_gateway,
            market_portfolio_audit_alert_notifier=self.mock_audit_notifier,
            market_portfolio_audit_compliance_hub=self.mock_compliance_hub,
            market_portfolio_audit_log_exporter=self.mock_log_exporter,
            market_portfolio_autonomous_sentinel=self.mock_autonomous_sentinel,
            market_portfolio_backtest_evaluator_bridge=self.mock_backtest_evaluator,
            market_portfolio_backtester=self.mock_backtester,
            market_portfolio_collector_agent=self.mock_collector_agent,
            market_portfolio_data_exporter=self.mock_data_exporter,
            market_portfolio_digest=self.mock_digest,
            market_portfolio_dividend_tracker=self.mock_dividend_tracker,
            market_portfolio_event_intelligence_hub=self.mock_event_intelligence,
            market_portfolio_execution_cost_optimizer=self.mock_execution_cost_optimizer,
            market_portfolio_execution_pipeline=self.mock_execution_pipeline,
            market_portfolio_integration_hub=self.mock_integration_hub,
            market_portfolio_liquidity_scenario_analyzer=self.mock_liquidity_scenario_analyzer,
            market_portfolio_monitor=self.mock_portfolio_monitor,
            market_portfolio_performance_analytics=self.mock_performance_analytics,
            market_portfolio_predictive_aggregator=self.mock_predictive_aggregator,
            market_portfolio_scenario_simulator=self.mock_scenario_simulator,
            market_portfolio_slippage_model=self.mock_slippage_model,
            market_portfolio_strategy_optimizer=self.mock_strategy_optimizer,
            market_portfolio_stress_audit_visualizer=self.mock_stress_audit_visualizer,
            market_portfolio_stress_auto_rebalance_trigger=self.mock_stress_auto_rebalance_trigger,
            market_portfolio_stress_monte_carlo_engine=self.mock_stress_monte_carlo_engine,
            market_portfolio_stress_recovery_coordinator_bridge=self.mock_stress_recovery_coordinator,
            market_portfolio_stress_reporter=self.mock_stress_reporter,
            market_portfolio_stress_scenario_pipeline=self.mock_stress_scenario_pipeline,
            market_portfolio_tax_calculator=self.mock_tax_calculator,
            market_portfolio_telegram_command_center=self.mock_telegram_command_center,
            market_portfolio_telegram_notifier=self.mock_telegram_notifier,
            market_portfolio_valuation=self.mock_valuation,
            market_portfolio_var_liquidity_core=self.mock_var_liquidity_core,
            market_portfolio_visualizer_v2=self.mock_visualizer_v2,
            market_portfolio_webhook_event_logger=self.mock_webhook_event_logger,
            market_portfolio_webhook_sync=self.mock_webhook_sync,
            market_report_generator=self.mock_report_generator,
            market_sentiment_digest=self.mock_sentiment_digest,
            market_sentiment_risk_alert_bridge=self.mock_sentiment_risk_alert_bridge,
            market_sentiment_risk_hub=self.mock_sentiment_risk_hub,
            market_sentiment_telegram_publisher=self.mock_sentiment_telegram_publisher,
            market_telegram_pipeline=self.mock_telegram_pipeline
        )

        self.mock_portfolio_dispatcher.dispatch.assert_called()

if __name__ == '__main__':
    unittest.main()