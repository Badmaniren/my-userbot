import unittest
import uuid
import random
import os
import temp5
from skills.market_insider_activity_tracker import market_insider_activity_tracker
from skills.db_storage import db_storage
from skills.market_parser import market_parser
from skills.market_portfolio_alert_dispatcher import market_portfolio_alert_dispatcher
from skills.market_portfolio_alert_event_sink import market_portfolio_alert_event_sink
from skills.market_portfolio_alert_filter_router import market_portfolio_alert_filter_router
from skills.market_portfolio_api_gateway import market_portfolio_api_gateway
from skills.market_portfolio_audit_alert_notifier import market_portfolio_audit_alert_notifier
from skills.market_portfolio_audit_compliance_hub import market_portfolio_audit_compliance_hub
from skills.market_portfolio_audit_log_exporter import market_portfolio_audit_log_exporter
from skills.market_portfolio_autonomous_sentinel import market_portfolio_autonomous_sentinel
from skills.market_portfolio_backtest_evaluator_bridge import market_portfolio_backtest_evaluator_bridge
from skills.market_portfolio_backtester import market_portfolio_backtester
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_data_exporter import market_portfolio_data_exporter
from skills.market_portfolio_digest import market_portfolio_digest
from skills.market_portfolio_event_intelligence_hub import market_portfolio_event_intelligence_hub
from skills.market_portfolio_integration_hub import market_portfolio_integration_hub
from skills.market_portfolio_monitor import market_portfolio_monitor
from skills.market_portfolio_performance_analytics import market_portfolio_performance_analytics
from skills.market_portfolio_predictive_aggregator import market_portfolio_predictive_aggregator
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_strategy_optimizer import market_portfolio_strategy_optimizer
from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter
from skills.market_portfolio_telegram_command_center import market_portfolio_telegram_command_center
from skills.market_portfolio_telegram_notifier import market_portfolio_telegram_notifier
from skills.market_portfolio_valuation import market_portfolio_valuation
from skills.market_portfolio_visualizer_v2 import market_portfolio_visualizer_v2
from skills.market_portfolio_webhook_event_logger import market_portfolio_webhook_event_logger
from skills.market_portfolio_webhook_sync import market_portfolio_webhook_sync
from skills.market_report_generator import market_report_generator
from skills.market_telegram_pipeline import market_telegram_pipeline
from skills.extractor_tool_1790087207 import extractor_tool_1790087207
from skills.extractor_tool_1790102839 import extractor_tool_1790102839

class TestMarketInsiderActivityTrackerIntegration(unittest.TestCase):
    def test_insider_activity_tracker_end_to_end(self):
        random_ticker_id = str(uuid.uuid4())
        random_volume = round(random.uniform(10000.0, 999999.0), 2)
        random_threshold = round(random.uniform(1.5, 10.0), 2)

        raw_market_data = market_parser.parse({
            "ticker_id": random_ticker_id,
            "volume": random_volume
        })

        extracted_data_1 = extractor_tool_1790087207.extract(raw_market_data)
        extracted_data_2 = extractor_tool_1790102839.extract(raw_market_data)

        collector_payload = market_portfolio_collector_agent.collect({
            "ticker_id": random_ticker_id,
            "ext_1": extracted_data_1,
            "ext_2": extracted_data_2
        })

        db_storage.save_market_data(collector_payload)

        monitor_status = market_portfolio_monitor.check_status(random_ticker_id)
        self.assertIsNotNone(monitor_status)

        insider_result = market_insider_activity_tracker.track_activity({
            "ticker_id": random_ticker_id,
            "volume": random_volume,
            "anomaly_multiplier": random_threshold,
            "source_data": collector_payload
        })

        self.assertIn("anomaly_detected", insider_result)
        self.assertEqual(insider_result.get("ticker_id"), random_ticker_id)

        filtered_alert = market_portfolio_alert_filter_router.route(insider_result)
        
        if filtered_alert:
            dispatch_response = market_portfolio_alert_dispatcher.dispatch(filtered_alert)
            self.assertTrue(dispatch_response)
            
            event_sink_res = market_portfolio_alert_event_sink.record(filtered_alert)
            self.assertIsNotNone(event_sink_res)

            audit_notif = market_portfolio_audit_alert_notifier.notify(filtered_alert)
            self.assertTrue(audit_notif)

            compliance_res = market_portfolio_audit_compliance_hub.verify(filtered_alert)
            self.assertIsNotNone(compliance_res)

            log_export_path = f"test_audit_log_{uuid.uuid4()}.json"
            market_portfolio_audit_log_exporter.export(filtered_alert, log_export_path)
            self.assertTrue(os.path.exists(log_export_path))
            os.remove(log_export_path)

        hub_data = market_portfolio_integration_hub.sync(insider_result)
        self.assertIsNotNone(hub_data)

        eval_bridge = market_portfolio_backtest_evaluator_bridge.evaluate(insider_result)
        self.assertIsNotNone(eval_bridge)

        backtest_res = market_portfolio_backtester.run(random_ticker_id)
        self.assertIsNotNone(backtest_res)

        perf_data = market_portfolio_performance_analytics.analyze(random_ticker_id)
        self.assertIsNotNone(perf_data)

        pred_agg = market_portfolio_predictive_aggregator.aggregate(random_ticker_id)
        self.assertIsNotNone(pred_agg)

        sim_res = market_portfolio_scenario_simulator.simulate(random_ticker_id)
        self.assertIsNotNone(sim_res)

        opt_res = market_portfolio_strategy_optimizer.optimize(random_ticker_id)
        self.assertIsNotNone(opt_res)

        stress_rep = market_portfolio_stress_reporter.generate(random_ticker_id)
        self.assertIsNotNone(stress_rep)

        val_res = market_portfolio_valuation.compute(random_ticker_id)
        self.assertIsNotNone(val_res)

        viz_output = f"test_visualizer_{uuid.uuid4()}.png"
        market_portfolio_visualizer_v2.render(insider_result, viz_output)
        self.assertTrue(os.path.exists(viz_output))
        os.remove(viz_output)

        webhook_log = market_portfolio_webhook_event_logger.log(insider_result)
        self.assertIsNotNone(webhook_log)

        webhook_sync_res = market_portfolio_webhook_sync.sync(webhook_log)
        self.assertTrue(webhook_sync_res)

        report_file = f"test_market_report_{uuid.uuid4()}.pdf"
        market_report_generator.generate(random_ticker_id, report_file)
        self.assertTrue(os.path.exists(report_file))
        os.remove(report_file)

        digest_payload = market_portfolio_digest.compile([insider_result])
        self.assertIsNotNone(digest_payload)

        telegram_msg = market_portfolio_telegram_notifier.send(digest_payload)
        self.assertTrue(telegram_msg)

        sentinel_res = market_portfolio_autonomous_sentinel.pulse()
        self.assertIsNotNone(sentinel_res)

        api_gateway_res = market_portfolio_api_gateway.forward(insider_result)
        self.assertEqual(api_gateway_res.get("status"), 200)

        cmd_center_res = market_portfolio_telegram_command_center.process_command(f"/status {random_ticker_id}")
        self.assertIsNotNone(cmd_center_res)

        pipeline_res = market_telegram_pipeline.execute(random_ticker_id)
        self.assertTrue(pipeline_res)

if __name__ == "__main__":
    unittest.main()