import unittest
import uuid
import random
import os
from skills.market_macro_liquidity_monitor_v2 import (
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
    market_portfolio_stress_auto_rebalance_trigger,
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

class TestMarketMacroLiquidityMonitorV2Integration(unittest.TestCase):
    def test_macro_liquidity_monitor_integration(self):
        random_session_id = str(uuid.uuid4())
        random_liquidity_factor = random.uniform(0.1, 10.0)
        test_output_filepath = f"macro_liquidity_report_{random_session_id}.json"

        try:
            parsed_data = market_parser.run(session_id=random_session_id, factor=random_liquidity_factor)

            sentiment_data = market_news_sentiment_analyzer.run(data=parsed_data)

            anomaly_results = market_anomaly_detector.run(
                input_metrics=sentiment_data,
                threshold=random_liquidity_factor
            )

            var_core_result = market_portfolio_var_liquidity_core.run(
                anomaly_payload=anomaly_results,
                session_id=random_session_id
            )

            db_storage.save(
                record_id=random_session_id,
                payload=var_core_result
            )

            report_result = market_report_generator.run(
                session_id=random_session_id,
                output_path=test_output_filepath
            )

            self.assertTrue(
                os.path.exists(test_output_filepath),
                f"Integration failure: Expected report file {test_output_filepath} was not generated."
            )

            self.assertIsNotNone(report_result)

        finally:
            if os.path.exists(test_output_filepath):
                try:
                    os.remove(test_output_filepath)
                except OSError:
                    pass

if __name__ == "__main__":
    unittest.main()