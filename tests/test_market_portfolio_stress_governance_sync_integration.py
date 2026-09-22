import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_stress_governance_sync import (
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

class TestMarketPortfolioStressGovernanceSyncIntegration(unittest.TestCase):

    def setUp(self):
        self.test_run_id = str(uuid.uuid4())
        self.random_portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        self.random_stress_factor = round(random.uniform(0.05, 0.95), 4)
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_end_to_end_stress_governance_pipeline(self):
        payload = {
            "run_id": self.test_run_id,
            "portfolio_value": self.random_portfolio_value,
            "stress_factor": self.random_stress_factor,
            "export_path": os.path.join(self.temp_dir.name, f"report_{self.test_run_id}.json")
        }

        # Вызываем реальные компоненты без моков для сквозной интеграции
        parsed_data = market_parser.parse(payload)
        self.assertIsNotNone(parsed_data)

        db_result = db_storage.save_transaction(parsed_data)
        self.assertIn("status", db_result)

        simulated_scenario = market_portfolio_scenario_simulator.run(db_result)
        self.assertEqual(simulated_scenario.get("run_id"), self.test_run_id)

        valuation_res = market_portfolio_valuation.calculate(simulated_scenario)
        self.assertGreaterEqual(valuation_res.get("valuation"), 0.0)

        report_output = market_report_generator.generate(valuation_res)
        self.assertTrue(os.path.exists(payload["export_path"]) or isinstance(report_output, dict))

        alert_payload = {
            "id": str(uuid.uuid4()),
            "run_id": self.test_run_id,
            "severity": "HIGH" if self.random_stress_factor > 0.5 else "LOW"
        }

        filtered_alert = market_portfolio_alert_filter_router.route(alert_payload)
        dispatched_alert = market_portfolio_alert_dispatcher.dispatch(filtered_alert)
        sink_result = market_portfolio_alert_event_sink.sink(dispatched_alert)

        self.assertEqual(sink_result.get("run_id"), self.test_run_id)

        audit_res = market_portfolio_audit_compliance_hub.verify(sink_result)
        self.assertTrue(audit_res.get("compliant", True))

        exporter_res = market_portfolio_audit_log_exporter.export(audit_res)
        self.assertIsNotNone(exporter_res)

        # Проверяем работу мониторинга и сентинела
        sentinel_status = market_portfolio_autonomous_sentinel.check()
        self.assertIsInstance(sentinel_status, dict)

        monitor_metrics = market_portfolio_monitor.collect()
        self.assertIsInstance(monitor_metrics, dict)

        # Финализация через шлюз и интеграционный хаб
        gateway_response = market_portfolio_api_gateway.handle({
            "run_id": self.test_run_id,
            "action": "SYNC_GOVERNANCE_COMPLETE"
        })
        self.assertEqual(gateway_response.get("run_id"), self.test_run_id)

        integration_result = market_portfolio_integration_hub.sync(gateway_response)
        self.assertIsNotNone(integration_result)

if __name__ == "__main__":
    unittest.main()