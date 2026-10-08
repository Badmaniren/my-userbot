import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.market_portfolio_stress_audit_pdf_exporter import start_new


class TestMarketPortfolioStressAuditPdfExporter(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_tool_1 = MagicMock()
        self.extractor_tool_2 = MagicMock()
        self.extractor_tool_3 = MagicMock()
        self.extractor_tool_4 = MagicMock()
        self.market_anomaly_detector = MagicMock()
        self.market_insider_activity_tracker = MagicMock()
        self.market_insider_alert_pipeline = MagicMock()
        self.market_insider_anomaly_analyzer = MagicMock()
        self.market_insider_anomaly_report_bridge = MagicMock()
        self.market_news_sentiment_analyzer = MagicMock()
        self.market_parser = MagicMock()
        self.market_portfolio_alert_dispatcher = MagicMock()
        self.market_portfolio_alert_event_sink = MagicMock()
        self.market_portfolio_alert_filter_router = MagicMock()
        self.market_portfolio_api_gateway = MagicMock()
        self.market_portfolio_audit_alert_notifier = MagicMock()
        self.market_portfolio_audit_compliance_hub = MagicMock()
        self.market_portfolio_audit_log_exporter = MagicMock()
        self.market_portfolio_autonomous_sentinel = MagicMock()
        self.market_portfolio_backtest_evaluator_bridge = MagicMock()
        self.market_portfolio_backtester = MagicMock()
        self.market_portfolio_collector_agent = MagicMock()
        self.market_portfolio_data_exporter = MagicMock()
        self.market_portfolio_digest = MagicMock()
        self.market_portfolio_dividend_tracker = MagicMock()
        self.market_portfolio_event_intelligence_hub = MagicMock()
        self.market_portfolio_execution_cost_optimizer = MagicMock()
        self.market_portfolio_execution_pipeline = MagicMock()
        self.market_portfolio_integration_hub = MagicMock()
        self.market_portfolio_liquidity_scenario_analyzer = MagicMock()
        self.market_portfolio_monitor = MagicMock()
        self.market_portfolio_performance_analytics = MagicMock()
        self.market_portfolio_predictive_aggregator = MagicMock()
        self.market_portfolio_scenario_simulator = MagicMock()
        self.market_portfolio_slippage_model = MagicMock()
        self.market_portfolio_strategy_optimizer = MagicMock()
        self.market_portfolio_stress_audit_summary_vault = MagicMock()
        self.market_portfolio_stress_audit_visualizer = MagicMock()
        self.market_portfolio_stress_auto_rebalance_trigger = MagicMock()
        self.market_portfolio_stress_monte_carlo_engine = MagicMock()
        self.market_portfolio_stress_recovery_coordinator_bridge = MagicMock()
        self.market_portfolio_stress_reporter = MagicMock()
        self.market_portfolio_stress_scenario_matrix_evaluator = MagicMock()
        self.market_portfolio_stress_scenario_pipeline = MagicMock()
        self.market_portfolio_tax_calculator = MagicMock()
        self.market_portfolio_telegram_command_center = MagicMock()
        self.market_portfolio_telegram_notifier = MagicMock()
        self.market_portfolio_valuation = MagicMock()
        self.market_portfolio_var_liquidity_core = MagicMock()
        self.market_portfolio_visualizer_v2 = MagicMock()
        self.market_portfolio_webhook_event_logger = MagicMock()
        self.market_portfolio_webhook_sync = MagicMock()
        self.market_report_generator = MagicMock()
        self.market_sentiment_digest = MagicMock()
        self.market_sentiment_risk_alert_bridge = MagicMock()
        self.market_sentiment_risk_hub = MagicMock()
        self.market_sentiment_telegram_publisher = MagicMock()
        self.market_telegram_pipeline = MagicMock()

    def test_start_new_success_flow(self):
        rand_audit_id = uuid.uuid4().hex
        rand_pdf_path = f"/tmp/{uuid.uuid4().hex}.pdf"
        rand_binary_content = uuid.uuid4().bytes

        self.db_storage.fetch_audit_data.return_value = {
            "audit_id": rand_audit_id,
            "metrics": [random.uniform(0, 100) for _ in range(3)]
        }
        self.market_report_generator.generate_pdf.return_value = rand_binary_content

        with patch("skills.market_portfolio_stress_audit_pdf_exporter.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            result = start_new(
                db_storage=self.db_storage,
                extractor_tool_1790087207=self.extractor_tool_1,
                extractor_tool_1790102839=self.extractor_tool_2,
                extractor_tool_1790262909=self.extractor_tool_3,
                extractor_tool_1790621808=self.extractor_tool_4,
                market_anomaly_detector=self.market_anomaly_detector,
                market_insider_activity_tracker=self.market_insider_activity_tracker,
                market_insider_alert_pipeline=self.market_insider_alert_pipeline,
                market_insider_anomaly_analyzer=self.market_insider_anomaly_analyzer,
                market_insider_anomaly_report_bridge=self.market_insider_anomaly_report_bridge,
                market_news_sentiment_analyzer=self.market_news_sentiment_analyzer,
                market_parser=self.market_parser,
                market_portfolio_alert_dispatcher=self.market_portfolio_alert_dispatcher,
                market_portfolio_alert_event_sink=self.market_portfolio_alert_event_sink,
                market_portfolio_alert_filter_router=self.market_portfolio_alert_filter_router,
                market_portfolio_api_gateway=self.market_portfolio_api_gateway,
                market_portfolio_audit_alert_notifier=self.market_portfolio_audit_alert_notifier,
                market_portfolio_audit_compliance_hub=self.market_portfolio_audit_compliance_hub,
                market_portfolio_audit_log_exporter=self.market_portfolio_audit_log_exporter,
                market_portfolio_autonomous_sentinel=self.market_portfolio_autonomous_sentinel,
                market_portfolio_backtest_evaluator_bridge=self.market_portfolio_backtest_evaluator_bridge,
                market_portfolio_backtester=self.market_portfolio_backtester,
                market_portfolio_collector_agent=self.market_portfolio_collector_agent,
                market_portfolio_data_exporter=self.market_portfolio_data_exporter,
                market_portfolio_digest=self.market_portfolio_digest,
                market_portfolio_dividend_tracker=self.market_portfolio_dividend_tracker,
                market_portfolio_event_intelligence_hub=self.market_portfolio_event_intelligence_hub,
                market_portfolio_execution_cost_optimizer=self.market_portfolio_execution_cost_optimizer,
                market_portfolio_execution_pipeline=self.market_portfolio_execution_pipeline,
                market_portfolio_integration_hub=self.market_portfolio_integration_hub,
                market_portfolio_liquidity_scenario_analyzer=self.market_portfolio_liquidity_scenario_analyzer,
                market_portfolio_monitor=self.market_portfolio_monitor,
                market_portfolio_performance_analytics=self.market_portfolio_performance_analytics,
                market_portfolio_predictive_aggregator=self.market_portfolio_predictive_aggregator,
                market_portfolio_scenario_simulator=self.market_portfolio_scenario_simulator,
                market_portfolio_slippage_model=self.market_portfolio_slippage_model,
                market_portfolio_strategy_optimizer=self.market_portfolio_strategy_optimizer,
                market_portfolio_stress_audit_summary_vault=self.market_portfolio_stress_audit_summary_vault,
                market_portfolio_stress_audit_visualizer=self.market_portfolio_stress_audit_visualizer,
                market_portfolio_stress_auto_rebalance_trigger=self.market_portfolio_stress_auto_rebalance_trigger,
                market_portfolio_stress_monte_carlo_engine=self.market_portfolio_stress_monte_carlo_engine,
                market_portfolio_stress_recovery_coordinator_bridge=self.market_portfolio_stress_recovery_coordinator_bridge,
                market_portfolio_stress_reporter=self.market_portfolio_stress_reporter,
                market_portfolio_stress_scenario_matrix_evaluator=self.market_portfolio_stress_scenario_matrix_evaluator,
                market_portfolio_stress_scenario_pipeline=self.market_portfolio_stress_scenario_pipeline,
                market_portfolio_tax_calculator=self.market_portfolio_tax_calculator,
                market_portfolio_telegram_command_center=self.market_portfolio_telegram_command_center,
                market_portfolio_telegram_notifier=self.market_portfolio_telegram_notifier,
                market_portfolio_valuation=self.market_portfolio_valuation,
                market_portfolio_var_liquidity_core=self.market_portfolio_var_liquidity_core,
                market_portfolio_visualizer_v2=self.market_portfolio_visualizer_v2,
                market_portfolio_webhook_event_logger=self.market_portfolio_webhook_event_logger,
                market_portfolio_webhook_sync=self.market_portfolio_webhook_sync,
                market_report_generator=self.market_report_generator,
                market_sentiment_digest=self.market_sentiment_digest,
                market_sentiment_risk_alert_bridge=self.market_sentiment_risk_alert_bridge,
                market_sentiment_risk_hub=self.market_sentiment_risk_hub,
                market_sentiment_telegram_publisher=self.market_sentiment_telegram_publisher,
                market_telegram_pipeline=self.market_telegram_pipeline
            )

            self.db_storage.fetch_audit_data.assert_called_once()
            self.market_report_generator.generate_pdf.assert_called_once()
            mock_file.write.assert_called_once_with(rand_binary_content)

    def test_start_new_handles_missing_audit_data(self):
        self.db_storage.fetch_audit_data.return_value = None

        with self.assertRaises(Exception):
            start_new(
                db_storage=self.db_storage,
                extractor_tool_1790087207=self.extractor_tool_1,
                extractor_tool_1790102839=self.extractor_tool_2,
                extractor_tool_1790262909=self.extractor_tool_3,
                extractor_tool_1790621808=self.extractor_tool_4,
                market_anomaly_detector=self.market_anomaly_detector,
                market_insider_activity_tracker=self.market_insider_activity_tracker,
                market_insider_alert_pipeline=self.market_insider_alert_pipeline,
                market_insider_anomaly_analyzer=self.market_insider_anomaly_analyzer,
                market_insider_anomaly_report_bridge=self.market_insider_anomaly_report_bridge,
                market_news_sentiment_analyzer=self.market_news_sentiment_analyzer,
                market_parser=self.market_parser,
                market_portfolio_alert_dispatcher=self.market_portfolio_alert_dispatcher,
                market_portfolio_alert_event_sink=self.market_portfolio_alert_event_sink,
                market_portfolio_alert_filter_router=self.market_portfolio_alert_filter_router,
                market_portfolio_api_gateway=self.market_portfolio_api_gateway,
                market_portfolio_audit_alert_notifier=self.market_portfolio_audit_alert_notifier,
                market_portfolio_audit_compliance_hub=self.market_portfolio_audit_compliance_hub,
                market_portfolio_audit_log_exporter=self.market_portfolio_audit_log_exporter,
                market_portfolio_autonomous_sentinel=self.market_portfolio_autonomous_sentinel,
                market_portfolio_backtest_evaluator_bridge=self.market_portfolio_backtest_evaluator_bridge,
                market_portfolio_backtester=self.market_portfolio_backtester,
                market_portfolio_collector_agent=self.market_portfolio_collector_agent,
                market_portfolio_data_exporter=self.market_portfolio_data_exporter,
                market_portfolio_digest=self.market_portfolio_digest,
                market_portfolio_dividend_tracker=self.market_portfolio_dividend_tracker,
                market_portfolio_event_intelligence_hub=self.market_portfolio_event_intelligence_hub,
                market_portfolio_execution_cost_optimizer=self.market_portfolio_execution_cost_optimizer,
                market_portfolio_execution_pipeline=self.market_portfolio_execution_pipeline,
                market_portfolio_integration_hub=self.market_portfolio_integration_hub,
                market_portfolio_liquidity_scenario_analyzer=self.market_portfolio_liquidity_scenario_analyzer,
                market_portfolio_monitor=self.market_portfolio_monitor,
                market_portfolio_performance_analytics=self.market_portfolio_performance_analytics,
                market_portfolio_predictive_aggregator=self.market_portfolio_predictive_aggregator,
                market_portfolio_scenario_simulator=self.market_portfolio_scenario_simulator,
                market_portfolio_slippage_model=self.market_portfolio_slippage_model,
                market_portfolio_strategy_optimizer=self.market_portfolio_strategy_optimizer,
                market_portfolio_stress_audit_summary_vault=self.market_portfolio_stress_audit_summary_vault,
                market_portfolio_stress_audit_visualizer=self.market_portfolio_stress_audit_visualizer,
                market_portfolio_stress_auto_rebalance_trigger=self.market_portfolio_stress_auto_rebalance_trigger,
                market_portfolio_stress_monte_carlo_engine=self.market_portfolio_stress_monte_carlo_engine,
                market_portfolio_stress_recovery_coordinator_bridge=self.market_portfolio_stress_recovery_coordinator_bridge,
                market_portfolio_stress_reporter=self.market_portfolio_stress_reporter,
                market_portfolio_stress_scenario_matrix_evaluator=self.market_portfolio_stress_scenario_matrix_evaluator,
                market_portfolio_stress_scenario_pipeline=self.market_portfolio_stress_scenario_pipeline,
                market_portfolio_tax_calculator=self.market_portfolio_tax_calculator,
                market_portfolio_telegram_command_center=self.market_portfolio_telegram_command_center,
                market_portfolio_telegram_notifier=self.market_portfolio_telegram_notifier,
                market_portfolio_valuation=self.market_portfolio_valuation,
                market_portfolio_var_liquidity_core=self.market_portfolio_var_liquidity_core,
                market_portfolio_visualizer_v2=self.market_portfolio_visualizer_v2,
                market_portfolio_webhook_event_logger=self.market_portfolio_webhook_event_logger,
                market_portfolio_webhook_sync=self.market_portfolio_webhook_sync,
                market_report_generator=self.market_report_generator,
                market_sentiment_digest=self.market_sentiment_digest,
                market_sentiment_risk_alert_bridge=self.market_sentiment_risk_alert_bridge,
                market_sentiment_risk_hub=self.market_sentiment_risk_hub,
                market_sentiment_telegram_publisher=self.market_sentiment_telegram_publisher,
                market_telegram_pipeline=self.market_telegram_pipeline
            )


if __name__ == "__main__":
    unittest.main()