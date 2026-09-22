import unittest
import uuid
import random
import os
import tempfile

from skills.market_portfolio_insider_tracker import (
    db_storage,
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

class TestMarketPortfolioInsiderTrackerIntegration(unittest.TestCase):
    def test_insider_tracker_end_to_end_pipeline(self):
        random_ticker_id = f"TICKER_{uuid.uuid4().hex[:8]}"
        random_volume = random.randint(10000, 500000)
        random_price = round(random.uniform(10.0, 1000.0), 2)

        db_instance = db_storage()
        self.assertIsNotNone(db_instance)

        parser_instance = market_parser()
        raw_data = parser_instance.parse(random_ticker_id, random_volume, random_price)
        self.assertIsNotNone(raw_data)

        collector = market_portfolio_collector_agent()
        collected_payload = collector.collect(raw_data)
        self.assertIn(random_ticker_id, str(collected_payload))

        event_hub = market_portfolio_event_intelligence_hub()
        processed_event = event_hub.process(collected_payload)

        filter_router = market_portfolio_alert_filter_router()
        routed_signal = filter_router.route(processed_event)

        dispatcher = market_portfolio_alert_dispatcher()
        dispatch_result = dispatcher.dispatch(routed_signal)
        self.assertTrue(dispatch_result)

        sink = market_portfolio_alert_event_sink()
        sink_status = sink.record(dispatch_result)
        self.assertIsNotNone(sink_status)

        api_gateway = market_portfolio_api_gateway()
        api_response = api_gateway.get_status(random_ticker_id)
        self.assertIsNotNone(api_response)

        audit_hub = market_portfolio_audit_compliance_hub()
        audit_hub.verify(api_response)

        notifier = market_portfolio_audit_alert_notifier()
        notifier.notify(random_ticker_id)

        temp_dir = tempfile.gettempdir()
        export_file_path = os.path.join(temp_dir, f"audit_{uuid.uuid4().hex}.log")

        log_exporter = market_portfolio_audit_log_exporter()
        log_exporter.export(export_file_path)
        self.assertTrue(os.path.exists(export_file_path))

        sentinel = market_portfolio_autonomous_sentinel()
        sentinel.check()

        backtester = market_portfolio_backtester()
        backtest_res = backtester.run(random_ticker_id)

        bridge = market_portfolio_backtest_evaluator_bridge()
        bridge.evaluate(backtest_res)

        data_exporter = market_portfolio_data_exporter()
        exported_data = data_exporter.dump(random_ticker_id)
        self.assertIsNotNone(exported_data)

        digest = market_portfolio_digest()
        digest_output = digest.generate([random_ticker_id])
        self.assertIsNotNone(digest_output)

        integration_hub = market_portfolio_integration_hub()
        integration_hub.sync()

        monitor = market_portfolio_monitor()
        monitor.pulse()

        analytics = market_portfolio_performance_analytics()
        analytics.compute(random_ticker_id)

        aggregator = market_portfolio_predictive_aggregator()
        aggregator.aggregate(random_ticker_id)

        simulator = market_portfolio_scenario_simulator()
        simulator.simulate(random_ticker_id)

        optimizer = market_portfolio_strategy_optimizer()
        optimizer.optimize(random_ticker_id)

        stress_reporter = market_portfolio_stress_reporter()
        stress_reporter.generate_report()

        command_center = market_portfolio_telegram_command_center()
        command_center.handle(random_ticker_id)

        telegram_notifier = market_portfolio_telegram_notifier()
        telegram_notifier.send(random_ticker_id)

        valuation = market_portfolio_valuation()
        valuation.calculate(random_ticker_id)

        visualizer = market_portfolio_visualizer_v2()
        visualizer.render(random_ticker_id)

        event_logger = market_portfolio_webhook_event_logger()
        event_logger.log(random_ticker_id)

        webhook_sync = market_portfolio_webhook_sync()
        webhook_sync.trigger()

        report_generator = market_report_generator()
        report_generator.build()

        telegram_pipeline = market_telegram_pipeline()
        pipeline_status = telegram_pipeline.execute(random_ticker_id)
        self.assertIsNotNone(pipeline_status)

if __name__ == '__main__':
    unittest.main()