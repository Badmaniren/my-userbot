import unittest
import uuid
import random
import os
from skills.market_anomaly_score_calculator import (
    db_storage,
    extractor_tool_1790087207,
    extractor_tool_1790102839,
    market_insider_activity_tracker,
    market_parser,
    market_portfolio_alert_dispatcher,
    market_portfolio_alert_event_sink,
    market_portfolio_alert_filter_router,
    market_portfolio_anomaly_score_calculator,
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

class TestMarketAnomalyScoreCalculatorIntegration(unittest.TestCase):

    def test_end_to_end_anomaly_score_calculation(self):
        random_seed = random.randint(1000, 999999)
        market_id = f"market_test_{uuid.uuid4()}"
        asset_symbol = f"AST_{uuid.uuid4().hex[:6].upper()}"
        raw_volume = round(random.uniform(10000.0, 5000000.0), 2)
        insider_weight = round(random.uniform(0.1, 0.9), 4)

        parser_raw_data = market_parser(market_id=market_id, symbol=asset_symbol, volume=raw_volume, seed=random_seed)
        extracted_data_1 = extractor_tool_1790087207(input_data=parser_raw_data)
        extracted_data_2 = extractor_tool_1790102839(input_data=extracted_data_1)

        insider_metrics = market_insider_activity_tracker(symbol=asset_symbol, weight=insider_weight)

        collector_payload = market_portfolio_collector_agent(
            extracted_features=extracted_data_2,
            insider_activity=insider_metrics
        )

        storage_id = db_storage(payload=collector_payload, identifier=market_id)
        self.assertIsNotNone(storage_id)

        calculated_anomaly_score = market_portfolio_anomaly_score_calculator(
            storage_reference=storage_id,
            threshold=random.uniform(0.5, 0.9)
        )

        self.assertIsInstance(calculated_anomaly_score, (int, float))

        evaluation_bridge = market_portfolio_backtest_evaluator_bridge(score=calculated_anomaly_score)
        backtest_result = market_portfolio_backtester(bridge_data=evaluation_bridge)

        aggregator_output = market_portfolio_predictive_aggregator(backtest_results=backtest_result)
        monitoring_status = market_portfolio_monitor(input_signal=aggregator_output)

        self.assertIn(monitoring_status, ["ALERT", "NORMAL", "WARNING", True, False])

        alert_router = market_portfolio_alert_filter_router(status=monitoring_status, score=calculated_anomaly_score)
        event_sink = market_portfolio_alert_event_sink(route=alert_router)
        dispatcher_result = market_portfolio_alert_dispatcher(sink_data=event_sink)

        audit_hub = market_portfolio_audit_compliance_hub(dispatcher_status=dispatcher_result)
        audit_notifier = market_portfolio_audit_alert_notifier(compliance_data=audit_hub)
        audit_exporter = market_portfolio_audit_log_exporter(notifier_ref=audit_notifier)

        self.assertIsNotNone(audit_exporter)

        integration_result = market_portfolio_integration_hub(audit_log=audit_exporter)
        webhook_sync_status = market_portfolio_webhook_sync(sync_data=integration_result)
        webhook_logger = market_portfolio_webhook_event_logger(sync_status=webhook_sync_status)

        sentinel_check = market_portfolio_autonomous_sentinel(webhook_logger=webhook_logger)
        scenario_sim = market_portfolio_scenario_simulator(sentinel_state=sentinel_check)
        strategy_opt = market_portfolio_strategy_optimizer(scenario=scenario_sim)

        performance_data = market_portfolio_performance_analytics(strategy=strategy_opt)
        stress_report = market_portfolio_stress_reporter(analytics=performance_data)
        valuation_res = market_portfolio_valuation(stress_data=stress_report)

        data_export_path = f"export_{uuid.uuid4()}.json"
        exported_file = market_portfolio_data_exporter(valuation=valuation_res, filepath=data_export_path)

        self.assertTrue(os.path.exists(exported_file) or os.path.exists(data_export_path))

        if os.path.exists(data_export_path):
            os.remove(data_export_path)
        if exported_file and os.path.exists(exported_file):
            os.remove(exported_file)

        visualizer_ref = market_portfolio_visualizer_v2(valuation=valuation_res)
        report_output = market_report_generator(visualizer_data=visualizer_ref)
        digest_output = market_portfolio_digest(report=report_output)

        telegram_cmd = market_portfolio_telegram_command_center(digest=digest_output)
        telegram_notif = market_portfolio_telegram_notifier(command_center=telegram_cmd)
        pipeline_final = market_telegram_pipeline(notifier=telegram_notif)

        self.assertIsNotNone(pipeline_final)

if __name__ == '__main__':
    unittest.main()
