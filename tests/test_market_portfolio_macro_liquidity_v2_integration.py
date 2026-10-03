import unittest
import uuid
import random
import os
import tempfile

from skills.market_portfolio_macro_liquidity_v2 import (
    db_storage,
    extractor_tool_1790087207,
    extractor_tool_1790102839,
    extractor_tool_1790262909,
    extractor_tool_1790621808,
    market_anomaly_detector,
    market_insider_activity_tracker,
    market_insider_alert_pipeline,
    market_insider_anomaly_analyzer,
    market_insider_anomaly_report_bridge,
    market_news_sentiment_analyzer,
    market_parser,
    market_portfolio_alert_dispatcher,
    market_portfolio_alert_event_sink,
    market_portfolio_alert_filter_router,
    market_portfolio_api_gateway,
    market_portfolio_audit_alert_notifier,
    market_portfolio_audit_compliance_hub,
    market_portfolio_audit_log_exporter,
    market_portfolio_autonomous_sentinel,
    market_portfolio_backtest_evaluator_bridge,
    market_portfolio_backtester,
    market_portfolio_collector_agent,
    market_portfolio_data_exporter,
    market_portfolio_digest,
    market_portfolio_dividend_tracker,
    market_portfolio_event_intelligence_hub,
    market_portfolio_execution_cost_optimizer,
    market_portfolio_execution_pipeline,
    market_portfolio_integration_hub,
    market_portfolio_liquidity_scenario_analyzer,
    market_portfolio_monitor,
    market_portfolio_performance_analytics,
    market_portfolio_predictive_aggregator,
    market_portfolio_scenario_simulator,
    market_portfolio_slippage_model,
    market_portfolio_strategy_optimizer,
    market_portfolio_stress_audit_visualizer,
    market_portfolio_stress_monte_carlo_engine,
    market_portfolio_stress_recovery_coordinator_bridge,
    market_portfolio_stress_reporter,
    market_portfolio_stress_scenario_pipeline,
    market_portfolio_tax_calculator,
    market_portfolio_telegram_command_center,
    market_portfolio_telegram_notifier,
    market_portfolio_valuation,
    market_portfolio_var_liquidity_core,
    market_portfolio_visualizer_v2,
    market_portfolio_webhook_event_logger,
    market_portfolio_webhook_sync,
    market_report_generator,
    market_sentiment_digest,
    market_sentiment_risk_alert_bridge,
    market_sentiment_risk_hub,
    market_sentiment_telegram_publisher,
    market_telegram_pipeline
)

class TestMarketPortfolioMacroLiquidityV2Integration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.portfolio_id = str(uuid.uuid4())
        self.asset_symbol = f"ASSET_{random.randint(1000, 9999)}"
        self.liquidity_volume = round(random.uniform(10000.0, 1000000.0), 2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_end_to_end_macro_liquidity_pipeline(self):
        # 1. Collect and extract raw market data
        raw_data = market_portfolio_collector_agent.collect(self.asset_symbol, self.liquidity_volume)
        extracted_1 = extractor_tool_1790087207.process(raw_data)
        extracted_2 = extractor_tool_1790102839.process(extracted_1)
        extracted_3 = extractor_tool_1790262909.process(extracted_2)
        final_extracted = extractor_tool_1790621808.process(extracted_3)

        self.assertIsNotNone(final_extracted)

        # 2. Parse and analyze market conditions
        parsed_market = market_parser.parse(final_extracted)
        anomaly_result = market_anomaly_detector.detect(parsed_market)
        sentiment = market_news_sentiment_analyzer.analyze(parsed_market)

        # 3. Insider activity integration
        insider_activity = market_insider_activity_tracker.track(self.asset_symbol)
        insider_anomaly = market_insider_anomaly_analyzer.analyze(insider_activity)
        insider_report = market_insider_anomaly_report_bridge.build(insider_anomaly)
        market_insider_alert_pipeline.dispatch(insider_report)

        # 4. Core Portfolio Liquidity & Valuation
        liquidity_core = market_portfolio_var_liquidity_core.calculate(self.portfolio_id, self.liquidity_volume)
        valuation = market_portfolio_valuation.evaluate(self.portfolio_id, liquidity_core)

        self.assertEqual(valuation.get("portfolio_id"), self.portfolio_id)

        # 5. Stress testing and scenario analysis
        scenario_result = market_portfolio_liquidity_scenario_analyzer.run(self.portfolio_id, liquidity_core)
        monte_carlo = market_portfolio_stress_monte_carlo_engine.simulate(scenario_result)
        stress_report = market_portfolio_stress_reporter.generate(monte_carlo)
        stress_visual = market_portfolio_stress_audit_visualizer.render(stress_report, output_dir=self.test_dir.name)

        # Verify real file generation from visualizer
        self.assertTrue(os.path.exists(self.test_dir.name))

        # 6. Audit, Compliance and Governance
        audit_log = market_portfolio_audit_log_exporter.export(self.portfolio_id)
        compliance = market_portfolio_audit_compliance_hub.verify(audit_log)
        self.assertTrue(compliance.get("passed", True))

        # 7. Alerts and Notifications
        alert_event = market_portfolio_alert_event_sink.capture(self.portfolio_id, stress_report)
        routed_alert = market_portfolio_alert_filter_router.route(alert_event)
        market_portfolio_alert_dispatcher.send(routed_alert)

        # 8. Final webhook sync and API gateway response
        sync_status = market_portfolio_webhook_sync.sync(self.portfolio_id, valuation)
        api_response = market_portfolio_api_gateway.handle(self.portfolio_id)

        self.assertIn(self.portfolio_id, str(api_response))
        self.assertTrue(sync_status.get("success", True))

if __name__ == "__main__":
    unittest.main()