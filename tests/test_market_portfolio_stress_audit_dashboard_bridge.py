import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_stress_audit_dashboard_bridge import MarketPortfolioStressAuditDashboardBridge


class TestMarketPortfolioStressAuditDashboardBridge(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_1 = MagicMock()
        self.extractor_2 = MagicMock()
        self.extractor_3 = MagicMock()
        self.extractor_4 = MagicMock()
        self.anomaly_detector = MagicMock()
        self.insider_tracker = MagicMock()
        self.insider_alert = MagicMock()
        self.insider_anomaly = MagicMock()
        self.insider_report_bridge = MagicMock()
        self.news_sentiment = MagicMock()
        self.market_parser = MagicMock()
        self.portfolio_alert_dispatcher = MagicMock()
        self.portfolio_event_sink = MagicMock()
        self.portfolio_filter_router = MagicMock()
        self.portfolio_api_gateway = MagicMock()
        self.audit_alert_notifier = MagicMock()
        self.audit_compliance_hub = MagicMock()
        self.audit_log_exporter = MagicMock()
        self.autonomous_sentinel = MagicMock()
        self.backtest_evaluator_bridge = MagicMock()
        self.backtester = MagicMock()
        self.collector_agent = MagicMock()
        self.data_exporter = MagicMock()
        self.digest = MagicMock()
        self.dividend_tracker = MagicMock()
        self.event_intelligence_hub = MagicMock()
        self.execution_cost_optimizer = MagicMock()
        self.execution_pipeline = MagicMock()
        self.integration_hub = MagicMock()
        self.liquidity_scenario_analyzer = MagicMock()
        self.monitor = MagicMock()
        self.performance_analytics = MagicMock()
        self.predictive_aggregator = MagicMock()
        self.scenario_simulator = MagicMock()
        self.slippage_model = MagicMock()
        self.strategy_optimizer = MagicMock()
        self.stress_audit_summary_vault = MagicMock()
        self.stress_audit_visualizer = MagicMock()
        self.stress_auto_rebalance_trigger = MagicMock()
        self.stress_monte_carlo_engine = MagicMock()
        self.stress_recovery_coordinator_bridge = MagicMock()
        self.stress_reporter = MagicMock()
        self.stress_scenario_matrix_evaluator = MagicMock()
        self.stress_scenario_pipeline = MagicMock()
        self.tax_calculator = MagicMock()
        self.telegram_command_center = MagicMock()
        self.telegram_notifier = MagicMock()
        self.valuation = MagicMock()
        self.var_liquidity_core = MagicMock()
        self.visualizer_v2 = MagicMock()
        self.webhook_event_logger = MagicMock()
        self.webhook_sync = MagicMock()
        self.report_generator = MagicMock()
        self.sentiment_digest = MagicMock()
        self.sentiment_risk_alert_bridge = MagicMock()
        self.sentiment_risk_hub = MagicMock()
        self.sentiment_telegram_publisher = MagicMock()
        self.telegram_pipeline = MagicMock()

        self.bridge = MarketPortfolioStressAuditDashboardBridge(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_1,
            extractor_tool_1790102839=self.extractor_2,
            extractor_tool_1790262909=self.extractor_3,
            extractor_tool_1790621808=self.extractor_4,
            market_anomaly_detector=self.anomaly_detector,
            market_insider_activity_tracker=self.insider_tracker,
            market_insider_alert_pipeline=self.insider_alert,
            market_insider_anomaly_analyzer=self.insider_anomaly,
            market_insider_anomaly_report_bridge=self.insider_report_bridge,
            market_news_sentiment_analyzer=self.news_sentiment,
            market_parser=self.market_parser,
            market_portfolio_alert_dispatcher=self.portfolio_alert_dispatcher,
            market_portfolio_alert_event_sink=self.portfolio_event_sink,
            market_portfolio_alert_filter_router=self.portfolio_filter_router,
            market_portfolio_api_gateway=self.portfolio_api_gateway,
            market_portfolio_audit_alert_notifier=self.audit_alert_notifier,
            market_portfolio_audit_compliance_hub=self.audit_compliance_hub,
            market_portfolio_audit_log_exporter=self.audit_log_exporter,
            market_portfolio_autonomous_sentinel=self.autonomous_sentinel,
            market_portfolio_backtest_evaluator_bridge=self.backtest_evaluator_bridge,
            market_portfolio_backtester=self.backtester,
            market_portfolio_collector_agent=self.collector_agent,
            market_portfolio_data_exporter=self.data_exporter,
            market_portfolio_digest=self.digest,
            market_portfolio_dividend_tracker=self.dividend_tracker,
            market_portfolio_event_intelligence_hub=self.event_intelligence_hub,
            market_portfolio_execution_cost_optimizer=self.execution_cost_optimizer,
            market_portfolio_execution_pipeline=self.execution_pipeline,
            market_portfolio_integration_hub=self.integration_hub,
            market_portfolio_liquidity_scenario_analyzer=self.liquidity_scenario_analyzer,
            market_portfolio_monitor=self.monitor,
            market_portfolio_performance_analytics=self.performance_analytics,
            market_portfolio_predictive_aggregator=self.predictive_aggregator,
            market_portfolio_scenario_simulator=self.scenario_simulator,
            market_portfolio_slippage_model=self.slippage_model,
            market_portfolio_strategy_optimizer=self.strategy_optimizer,
            market_portfolio_stress_audit_summary_vault=self.stress_audit_summary_vault,
            market_portfolio_stress_audit_visualizer=self.stress_audit_visualizer,
            market_portfolio_stress_auto_rebalance_trigger=self.stress_auto_rebalance_trigger,
            market_portfolio_stress_monte_carlo_engine=self.stress_monte_carlo_engine,
            market_portfolio_stress_recovery_coordinator_bridge=self.stress_recovery_coordinator_bridge,
            market_portfolio_stress_reporter=self.stress_reporter,
            market_portfolio_stress_scenario_matrix_evaluator=self.stress_scenario_matrix_evaluator,
            market_portfolio_stress_scenario_pipeline=self.stress_scenario_pipeline,
            market_portfolio_tax_calculator=self.tax_calculator,
            market_portfolio_telegram_command_center=self.telegram_command_center,
            market_portfolio_telegram_notifier=self.telegram_notifier,
            market_portfolio_valuation=self.valuation,
            market_portfolio_var_liquidity_core=self.var_liquidity_core,
            market_portfolio_visualizer_v2=self.visualizer_v2,
            market_portfolio_webhook_event_logger=self.webhook_event_logger,
            market_portfolio_webhook_sync=self.webhook_sync,
            market_report_generator=self.report_generator,
            market_sentiment_digest=self.sentiment_digest,
            market_sentiment_risk_alert_bridge=self.sentiment_risk_alert_bridge,
            market_sentiment_risk_hub=self.sentiment_risk_hub,
            market_sentiment_telegram_publisher=self.sentiment_telegram_publisher,
            market_telegram_pipeline=self.telegram_pipeline
        )

    def test_aggregate_stress_dashboard_integrity(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_metric_val = random.uniform(1000.0, 99999.9)
        rand_status = random.choice(['OK', 'WARNING', 'CRITICAL', 'SECURE'])

        self.stress_monte_carlo_engine.run_simulation.return_value = {
            'portfolio_id': rand_portfolio_id,
            'var_95': rand_metric_val,
            'status': rand_status
        }
        self.stress_audit_summary_vault.fetch_summary.return_value = {
            'audit_id': uuid.uuid4().hex,
            'score': random.randint(0, 100)
        }

        dashboard_data = self.bridge.aggregate_dashboard(rand_portfolio_id)

        self.assertIn('portfolio_id', dashboard_data)
        self.assertEqual(dashboard_data['portfolio_id'], rand_portfolio_id)
        self.assertEqual(dashboard_data['var_95'], rand_metric_val)
        self.assertEqual(dashboard_data['status'], rand_status)
        self.stress_monte_carlo_engine.run_simulation.assert_called_once_with(rand_portfolio_id)

    def test_stream_chaos_metric_validation(self):
        garbage_bytes = ''.join(random.choices(string.ascii_letters + string.digits, k=128)).encode('utf-8')
        mock_stream = io.BytesIO(garbage_bytes)

        rand_key = uuid.uuid4().hex
        with patch('skills.market_portfolio_stress_audit_dashboard_bridge.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = mock_stream.read()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = self.bridge.ingest_external_stream(rand_key)
            self.assertIsNotNone(result)
            mock_get.assert_called_once()

    def test_anomaly_pipeline_failure_handling(self):
        rand_error_msg = uuid.uuid4().hex
        self.anomaly_detector.analyze.side_effect = ValueError(rand_error_msg)

        with self.assertRaises(ValueError) as ctx:
            self.bridge.process_anomaly_audit(uuid.uuid4().hex)

        self.assertIn(rand_error_msg, str(ctx.exception))

    def test_integrity_check_metrics_mismatch(self):
        rand_id = uuid.uuid4().hex
        expected_score = random.uniform(0, 1)

        self.var_liquidity_core.calculate.return_value = {'score': expected_score}
        self.stress_scenario_matrix_evaluator.evaluate.return_value = {'score': expected_score + 0.5}

        is_valid = self.bridge.verify_metric_integrity(rand_id)
        self.assertFalse(is_valid)

    def test_integrity_check_metrics_success(self):
        rand_id = uuid.uuid4().hex
        expected_score = random.uniform(0, 1)

        self.var_liquidity_core.calculate.return_value = {'score': expected_score}
        self.stress_scenario_matrix_evaluator.evaluate.return_value = {'score': expected_score}

        is_valid = self.bridge.verify_metric_integrity(rand_id)
        self.assertTrue(is_valid)