import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import string

from skills.market_portfolio_macro_liquidity_gate import MacroLiquidityGate


class TestMacroLiquidityGate(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_1 = MagicMock()
        self.extractor_2 = MagicMock()
        self.extractor_3 = MagicMock()
        self.extractor_4 = MagicMock()
        self.anomaly_detector = MagicMock()
        self.insider_tracker = MagicMock()
        self.alert_pipeline = MagicMock()
        self.anomaly_analyzer = MagicMock()
        self.report_bridge = MagicMock()
        self.news_sentiment = MagicMock()
        self.parser = MagicMock()
        self.alert_dispatcher = MagicMock()
        self.event_sink = MagicMock()
        self.filter_router = MagicMock()
        self.api_gateway = MagicMock()
        self.audit_notifier = MagicMock()
        self.compliance_hub = MagicMock()
        self.log_exporter = MagicMock()
        self.autonomous_sentinel = MagicMock()
        self.backtest_evaluator = MagicMock()
        self.backtester = MagicMock()
        self.collector_agent = MagicMock()
        self.data_exporter = MagicMock()
        self.digest = MagicMock()
        self.dividend_tracker = MagicMock()
        self.event_hub = MagicMock()
        self.execution_optimizer = MagicMock()
        self.execution_pipeline = MagicMock()
        self.integration_hub = MagicMock()
        self.liquidity_scenario = MagicMock()
        self.monitor = MagicMock()
        self.performance_analytics = MagicMock()
        self.predictive_aggregator = MagicMock()
        self.scenario_simulator = MagicMock()
        self.slippage_model = MagicMock()
        self.strategy_optimizer = MagicMock()
        self.stress_visualizer = MagicMock()
        self.stress_monte_carlo = MagicMock()
        self.stress_recovery = MagicMock()
        self.stress_reporter = MagicMock()
        self.stress_scenario_pipeline = MagicMock()
        self.tax_calculator = MagicMock()
        self.telegram_cmd = MagicMock()
        self.telegram_notifier = MagicMock()
        self.valuation = MagicMock()
        self.var_liquidity_core = MagicMock()
        self.visualizer_v2 = MagicMock()
        self.webhook_logger = MagicMock()
        self.webhook_sync = MagicMock()
        self.report_generator = MagicMock()
        self.sentiment_digest = MagicMock()
        self.risk_alert_bridge = MagicMock()
        self.risk_hub = MagicMock()
        self.telegram_publisher = MagicMock()
        self.telegram_pipeline = MagicMock()

        self.gate = MacroLiquidityGate(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_1,
            extractor_tool_1790102839=self.extractor_2,
            extractor_tool_1790262909=self.extractor_3,
            extractor_tool_1790621808=self.extractor_4,
            market_anomaly_detector=self.anomaly_detector,
            market_insider_activity_tracker=self.insider_tracker,
            market_insider_alert_pipeline=self.alert_pipeline,
            market_insider_anomaly_analyzer=self.anomaly_analyzer,
            market_insider_anomaly_report_bridge=self.report_bridge,
            market_news_sentiment_analyzer=self.news_sentiment,
            market_parser=self.parser,
            market_portfolio_alert_dispatcher=self.alert_dispatcher,
            market_portfolio_alert_event_sink=self.event_sink,
            market_portfolio_alert_filter_router=self.filter_router,
            market_portfolio_api_gateway=self.api_gateway,
            market_portfolio_audit_alert_notifier=self.audit_notifier,
            market_portfolio_audit_compliance_hub=self.compliance_hub,
            market_portfolio_audit_log_exporter=self.log_exporter,
            market_portfolio_autonomous_sentinel=self.autonomous_sentinel,
            market_portfolio_backtest_evaluator_bridge=self.backtest_evaluator,
            market_portfolio_backtester=self.backtester,
            market_portfolio_collector_agent=self.collector_agent,
            market_portfolio_data_exporter=self.data_exporter,
            market_portfolio_digest=self.digest,
            market_portfolio_dividend_tracker=self.dividend_tracker,
            market_portfolio_event_intelligence_hub=self.event_hub,
            market_portfolio_execution_cost_optimizer=self.execution_optimizer,
            market_portfolio_execution_pipeline=self.execution_pipeline,
            market_portfolio_integration_hub=self.integration_hub,
            market_portfolio_liquidity_scenario_analyzer=self.liquidity_scenario,
            market_portfolio_monitor=self.monitor,
            market_portfolio_performance_analytics=self.performance_analytics,
            market_portfolio_predictive_aggregator=self.predictive_aggregator,
            market_portfolio_scenario_simulator=self.scenario_simulator,
            market_portfolio_slippage_model=self.slippage_model,
            market_portfolio_strategy_optimizer=self.strategy_optimizer,
            market_portfolio_stress_audit_visualizer=self.stress_visualizer,
            market_portfolio_stress_monte_carlo_engine=self.stress_monte_carlo,
            market_portfolio_stress_recovery_coordinator_bridge=self.stress_recovery,
            market_portfolio_stress_reporter=self.stress_reporter,
            market_portfolio_stress_scenario_pipeline=self.stress_scenario_pipeline,
            market_portfolio_tax_calculator=self.tax_calculator,
            market_portfolio_telegram_command_center=self.telegram_cmd,
            market_portfolio_telegram_notifier=self.telegram_notifier,
            market_portfolio_valuation=self.valuation,
            market_portfolio_var_liquidity_core=self.var_liquidity_core,
            market_portfolio_visualizer_v2=self.visualizer_v2,
            market_portfolio_webhook_event_logger=self.webhook_logger,
            market_portfolio_webhook_sync=self.webhook_sync,
            market_report_generator=self.report_generator,
            market_sentiment_digest=self.sentiment_digest,
            market_sentiment_risk_alert_bridge=self.risk_alert_bridge,
            market_sentiment_risk_hub=self.risk_hub,
            market_sentiment_telegram_publisher=self.telegram_publisher,
            market_telegram_pipeline=self.telegram_pipeline
        )

    def test_aggregate_macro_liquidity_success(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_liquidity_metric = random.uniform(1000.0, 999999.0)
        rand_factor_name = "".join(random.choices(string.ascii_lowercase, k=10))

        self.extractor_1.extract.return_value = {rand_factor_name: rand_liquidity_metric}
        self.var_liquidity_core.calculate.return_value = rand_liquidity_metric * 0.95

        result = self.gate.aggregate_macro_liquidity(rand_portfolio_id)

        self.assertIsInstance(result, dict)
        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], rand_portfolio_id)
        self.assertIn("macro_liquidity_score", result)
        self.db_storage.save.assert_called_once()

    def test_aggregate_macro_liquidity_with_stream_data(self):
        rand_id = uuid.uuid4().hex
        rand_bytes = "".join(random.choices(string.ascii_letters, k=50)).encode('utf-8')
        mock_stream = io.BytesIO(rand_bytes)

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raw = mock_stream
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            self.parser.parse_stream.return_value = {"parsed_bytes_len": len(rand_bytes)}
            
            res = self.gate.process_external_stream(rand_id)
            self.assertEqual(res["status"], "success")
            self.parser.parse_stream.assert_called_once()

    def test_aggregate_macro_liquidity_exception_handling(self):
        rand_portfolio_id = uuid.uuid4().hex
        self.extractor_1.extract.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(Exception):
            self.gate.aggregate_macro_liquidity(rand_portfolio_id)
        
        self.audit_notifier.notify_error.assert_called_once()

    def test_liquidity_scenario_simulation_flow(self):
        rand_scenario_id = uuid.uuid4().hex
        rand_shock_value = random.uniform(-0.5, 0.5)

        self.liquidity_scenario.simulate.return_value = {
            "scenario_id": rand_scenario_id,
            "shock": rand_shock_value,
            "passed": True
        }

        res = self.gate.run_liquidity_scenario(rand_scenario_id, rand_shock_value)
        self.assertEqual(res["scenario_id"], rand_scenario_id)
        self.assertEqual(res["shock"], rand_shock_value)
        self.assertTrue(res["passed"])
        self.scenario_simulator.record.assert_called_once()