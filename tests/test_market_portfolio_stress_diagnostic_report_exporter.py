import unittest
from unittest.mock import MagicMock, patch
import io
import uuid
import random
import string

from skills.market_portfolio_stress_diagnostic_report_exporter import MarketPortfolioStressDiagnosticReportExporter

class TestMarketPortfolioStressDiagnosticReportExporter(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_1 = MagicMock()
        self.extractor_2 = MagicMock()
        self.extractor_3 = MagicMock()
        self.extractor_4 = MagicMock()
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

        self.exporter = MarketPortfolioStressDiagnosticReportExporter(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_1,
            extractor_tool_1790102839=self.extractor_2,
            extractor_tool_1790262909=self.extractor_3,
            extractor_tool_1790621808=self.extractor_4,
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

    def test_export_diagnostic_report_success(self):
        random_portfolio_id = uuid.uuid4().hex
        random_scenario_id = uuid.uuid4().hex
        expected_report_payload = ''.join(random.choices(string.ascii_letters + string.digits, k=32))

        self.market_portfolio_scenario_simulator.simulate.return_value = {
            "scenario_id": random_scenario_id,
            "status": "completed"
        }
        self.market_portfolio_stress_reporter.generate_report.return_value = expected_report_payload

        result = self.exporter.export_report(random_portfolio_id, random_scenario_id)

        self.assertEqual(result, expected_report_payload)
        self.market_portfolio_scenario_simulator.simulate.assert_called_once_with(random_portfolio_id, random_scenario_id)
        self.market_portfolio_stress_reporter.generate_report.assert_called_once()

    export_stream_path = f"/tmp/{uuid.uuid4().hex}.bin"
    def test_export_report_stream_io(self):
        random_portfolio_id = uuid.uuid4().hex
        random_scenario_id = uuid.uuid4().hex
        random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes

        self.market_portfolio_stress_reporter.generate_stream.return_value = io.BytesIO(random_bytes)

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            stream_result = self.exporter.export_to_stream(random_portfolio_id, random_scenario_id)

            self.assertIsInstance(stream_result, io.BytesIO)
            self.assertEqual(stream_result.read(), random_bytes)

    def test_database_persistence_integration(self):
        random_portfolio_id = uuid.uuid4().hex
        random_record_key = uuid.uuid4().hex
        random_record_value = random.randint(1000, 99999)

        self.db_storage.fetch_diagnostic_data.return_value = {
            random_record_key: random_record_value
        }

        data = self.exporter.fetch_diagnostic_data(random_portfolio_id)

        self.assertIn(random_record_key, data)
        self.assertEqual(data[random_record_key], random_record_value)
        self.db_storage.fetch_diagnostic_data.assert_called_once_with(random_portfolio_id)

    def test_alert_dispatch_on_critical_stress(self):
        random_portfolio_id = uuid.uuid4().hex
        random_alert_message = ''.join(random.choices(string.ascii_letters, k=20))

        self.market_portfolio_stress_monte_carlo_engine.evaluate_risk.return_value = {
            "critical": True,
            "message": random_alert_message
        }

        self.exporter.check_and_dispatch_stress_alerts(random_portfolio_id)

        self.market_portfolio_alert_dispatcher.dispatch.assert_called_once()
        args, _ = self.market_portfolio_alert_dispatcher.dispatch.call_args
        self.assertIn(random_alert_message, str(args))