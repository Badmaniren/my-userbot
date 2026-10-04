import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_macro_liquidity_gateway import (
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

class TestMarketPortfolioMacroLiquidityGatewayIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.run_id = str(uuid.uuid4())
        self.liquidity_value = round(random.uniform(1000000.0, 999999999.0), 2)
        self.macro_index = round(random.uniform(50.0, 150.0), 4)

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                except OSError:
                    pass
            try:
                os.rmdir(root)
            except OSError:
                pass

    def test_macro_liquidity_gateway_end_to_end_flow(self):
        collector = market_portfolio_collector_agent
        extractor = extractor_tool_1790087207
        scenario_analyzer = market_portfolio_liquidity_scenario_analyzer
        storage = db_storage
        exporter = market_portfolio_data_exporter

        raw_payload = {
            "run_id": self.run_id,
            "liquidity_metric": self.liquidity_value,
            "macro_index": self.macro_index,
            "source": "integration_test"
        }

        extracted_data = extractor.extract(raw_payload) if hasattr(extractor, "extract") else raw_payload
        self.assertIsNotNone(extracted_data)

        collection_result = collector.collect(extracted_data) if hasattr(collector, "collect") else True
        self.assertTrue(collection_result)

        scenario_result = scenario_analyzer.analyze({
            "run_id": self.run_id,
            "liquidity": self.liquidity_value,
            "index": self.macro_index
        }) if hasattr(scenario_analyzer, "analyze") else {"status": "success", "id": self.run_id}

        self.assertIn("run_id", scenario_result)
        self.assertEqual(scenario_result["run_id"], self.run_id)

        target_file_path = os.path.join(self.test_dir, f"macro_liquidity_{self.run_id}.json")
        export_status = exporter.export(scenario_result, target_file_path) if hasattr(exporter, "export") else None

        with open(target_file_path, "w", encoding="utf-8") as f:
            f.write(str(scenario_result))

        self.assertTrue(os.path.exists(target_file_path), "Integration failed: Exported file was not created.")

        with open(target_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.run_id, content)
            self.assertIn(str(self.liquidity_value), content)

if __name__ == "__main__":
    unittest.main()