import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_macro_liquidity_engine import MarketPortfolioMacroLiquidityEngine


class TestMarketPortfolioMacroLiquidityEngine(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_tool_1790087207 = MagicMock()
        self.extractor_tool_1790102839 = MagicMock()
        self.extractor_tool_1790262909 = MagicMock()
        self.extractor_tool_1790621808 = MagicMock()
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
        self.market_portfolio_stress_monte_carlo_engine = MagicMock()
        self.market_portfolio_stress_recovery_coordinator_bridge = MagicMock()
        self.market_portfolio_stress_reporter = MagicMock()
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

        self.engine = MarketPortfolioMacroLiquidityEngine(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_tool_1790087207,
            extractor_tool_1790102839=self.extractor_tool_1790102839,
            extractor_tool_1790262909=self.extractor_tool_1790262909,
            extractor_tool_1790621808=self.extractor_tool_1790621808,
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
            market_portfolio_stress_monte_carlo_engine=self.market_portfolio_stress_monte_carlo_engine,
            market_portfolio_stress_recovery_coordinator_bridge=self.market_portfolio_stress_recovery_coordinator_bridge,
            market_portfolio_stress_reporter=self.market_portfolio_stress_reporter,
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

    def test_compute_macro_liquidity_index_returns_randomized_metric(self):
        random_seed_val = random.randint(1000, 99999)
        expected_metric = round(random.uniform(0.0, 100.0), 4)
        
        self.market_portfolio_var_liquidity_core.compute_core.return_value = expected_metric

        result = self.engine.compute_macro_liquidity_index(random_seed_val)

        self.market_portfolio_var_liquidity_core.compute_core.assert_called_once_with(random_seed_val)
        self.assertEqual(result, expected_metric)

    def test_evaluate_market_liquidity_stream_with_byte_stream(self):
        random_garbage = uuid.uuid4().hex.encode('utf-8')
        mock_stream = io.BytesIO(random_garbage)

        random_asset_id = uuid.uuid4().hex
        self.market_parser.parse_stream.return_value = {random_asset_id: random.uniform(10.0, 500.0)}

        evaluation = self.engine.evaluate_market_liquidity_stream(mock_stream)

        self.assertIn(random_asset_id, evaluation)
        self.market_parser.parse_stream.assert_called_once()

    def test_dispatch_liquidity_anomaly_alert(self):
        anomaly_code = uuid.uuid4().hex
        severity_level = random.choice(['LOW', 'MEDIUM', 'CRITICAL', 'EXTREME'])
        
        self.engine.dispatch_liquidity_anomaly_alert(anomaly_code, severity_level)

        self.market_portfolio_alert_dispatcher.dispatch.assert_called_once()
        called_args = self.market_portfolio_alert_dispatcher.dispatch.call_args[0]
        self.assertIn(anomaly_code, str(called_args))
        self.assertIn(severity_level, str(called_args))

    def test_extract_macro_indicators_via_tools(self):
        tool_output_1 = uuid.uuid4().hex
        tool_output_2 = uuid.uuid4().hex
        tool_output_3 = uuid.uuid4().hex
        tool_output_4 = uuid.uuid4().hex

        self.extractor_tool_1790087207.extract.return_value = tool_output_1
        self.extractor_tool_1790102839.extract.return_value = tool_output_2
        self.extractor_tool_1790262909.extract.return_value = tool_output_3
        self.extractor_tool_1790621808.extract.return_value = tool_output_4

        aggregated = self.engine.extract_all_macro_indicators()

        self.assertEqual(aggregated['1790087207'], tool_output_1)
        self.assertEqual(aggregated['1790102839'], tool_output_2)
        self.assertEqual(aggregated['1790262909'], tool_output_3)
        self.assertEqual(aggregated['1790621808'], tool_output_4)

    def test_simulate_liquidity_stress_scenario(self):
        scenario_id = uuid.uuid4().hex
        shock_factor = round(random.uniform(0.01, 0.99), 5)
        expected_simulation_result = {uuid.uuid4().hex: random.randint(1, 1000)}

        self.market_portfolio_scenario_simulator.run_simulation.return_value = expected_simulation_result

        res = self.engine.simulate_liquidity_stress_scenario(scenario_id, shock_factor)

        self.market_portfolio_scenario_simulator.run_simulation.assert_called_once_with(scenario_id, shock_factor)
        self.assertEqual(res, expected_simulation_result)

    def test_audit_compliance_logging(self):
        event_tag = uuid.uuid4().hex
        payload_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_macro_liquidity_engine.uuid') as mock_uuid:
            mock_uuid.uuid4.return_value.hex = event_tag
            self.engine.log_audit_compliance_event(payload_data)

        self.market_portfolio_audit_compliance_hub.record.assert_called_once()
        recorded_payload = self.market_portfolio_audit_compliance_hub.record.call_args[0][0]
        self.assertEqual(recorded_payload['tag'], event_tag)
        self.assertEqual(recorded_payload['data'], payload_data)


if __name__ == '__main__':
    unittest.main()