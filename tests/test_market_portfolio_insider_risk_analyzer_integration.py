import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_insider_risk_analyzer import (
    db_storage,
    extractor_tool_1790087207,
    extractor_tool_1790102839,
    extractor_tool_1790262909,
    market_anomaly_detector,
    market_insider_activity_tracker,
    market_insider_alert_pipeline,
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
    market_portfolio_event_intelligence_hub,
    market_portfolio_integration_hub,
    market_portfolio_monitor,
    market_portfolio_performance_analytics,
    market_portfolio_predictive_aggregator,
    market_portfolio_scenario_simulator,
    market_portfolio_strategy_optimizer,
    market_portfolio_stress_reporter,
    market_portfolio_telegram_command_center,
    market_portfolio_telegram_notifier,
    market_portfolio_valuation,
    market_portfolio_visualizer_v2,
    market_portfolio_webhook_event_logger,
    market_portfolio_webhook_sync,
    market_report_generator,
    market_telegram_pipeline
)

class TestMarketPortfolioInsiderRiskAnalyzerIntegration(unittest.TestCase):
    def test_end_to_end_insider_risk_analysis_flow(self):
        random_portfolio_id = str(uuid.uuid4())
        random_ticker = f"TICK_{random.randint(1000, 9999)}"
        random_volume = random.uniform(10000.0, 500000.0)
        random_threshold = random.uniform(0.7, 0.99)

        # 1. Collect and Parse Market Data
        raw_data = market_parser.parse(ticker=random_ticker)
        collected_data = market_portfolio_collector_agent.collect(data=raw_data, portfolio_id=random_portfolio_id)
        
        # 2. Extract features using available tools
        feature_1 = extractor_tool_1790087207.extract(payload=collected_data)
        feature_2 = extractor_tool_1790102839.extract(payload=feature_1)
        refined_features = extractor_tool_1790262909.extract(payload=feature_2)

        # 3. Track Insider Activity and Detect Anomalies
        insider_activity = market_insider_activity_tracker.track(ticker=random_ticker, volume=random_volume)
        anomaly_result = market_anomaly_detector.detect(features=refined_features, activity=insider_activity)

        # 4. Run Risk Analysis through the target module without mocks
        analysis_report = market_portfolio_insider_risk_analyzer.analyze(
            portfolio_id=random_portfolio_id,
            ticker=random_ticker,
            anomaly_data=anomaly_result,
            threshold=random_threshold
        )

        self.assertIn("risk_score", analysis_report)
        self.assertEqual(analysis_report.get("portfolio_id"), random_portfolio_id)

        # 5. Persist via DB Storage and trigger pipelines
        db_storage.save(record_id=random_portfolio_id, data=analysis_report)
        alert_event = market_insider_alert_pipeline.process(report=analysis_report)
        
        filtered_alert = market_portfolio_alert_filter_router.route(event=alert_event)
        market_portfolio_alert_dispatcher.dispatch(alert=filtered_alert)
        market_portfolio_alert_event_sink.sink(event=filtered_alert)

        # 6. Compliance, Audit and Export verification
        audit_status = market_portfolio_audit_compliance_hub.verify(portfolio_id=random_portfolio_id)
        self.assertTrue(audit_status)

        market_portfolio_audit_alert_notifier.notify(portfolio_id=random_portfolio_id)
        
        export_file_path = os.path.join(tempfile.gettempdir(), f"audit_{random_portfolio_id}.log")
        market_portfolio_audit_log_exporter.export(destination=export_file_path, portfolio_id=random_portfolio_id)
        self.assertTrue(os.path.exists(export_file_path))

        # Cleanup test artifact
        if os.path.exists(export_file_path):
            os.remove(export_file_path)

if __name__ == "__main__":
    unittest.main()