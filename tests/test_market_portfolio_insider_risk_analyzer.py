import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
import json

from skills.market_portfolio_insider_risk_analyzer import MarketPortfolioInsiderRiskAnalyzer

class TestMarketPortfolioInsiderRiskAnalyzer(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_tool_1 = MagicMock()
        self.extractor_tool_2 = MagicMock()
        self.extractor_tool_3 = MagicMock()
        self.market_anomaly_detector = MagicMock()
        self.market_insider_activity_tracker = MagicMock()
        self.market_insider_alert_pipeline = MagicMock()
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
        self.market_portfolio_event_intelligence_hub = MagicMock()
        self.market_portfolio_integration_hub = MagicMock()
        self.market_portfolio_monitor = MagicMock()
        self.market_portfolio_performance_analytics = MagicMock()
        self.market_portfolio_predictive_aggregator = MagicMock()
        self.market_portfolio_scenario_simulator = MagicMock()
        self.market_portfolio_strategy_optimizer = MagicMock()
        self.market_portfolio_stress_reporter = MagicMock()
        self.market_portfolio_telegram_command_center = MagicMock()
        self.market_portfolio_telegram_notifier = MagicMock()
        self.market_portfolio_valuation = MagicMock()
        self.market_portfolio_visualizer_v2 = MagicMock()
        self.market_portfolio_webhook_event_logger = MagicMock()
        self.market_portfolio_webhook_sync = MagicMock()
        self.market_report_generator = MagicMock()
        self.market_telegram_pipeline = MagicMock()

        self.analyzer = MarketPortfolioInsiderRiskAnalyzer(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_tool_1,
            extractor_tool_1790102839=self.extractor_tool_2,
            extractor_tool_1790262909=self.extractor_tool_3,
            market_anomaly_detector=self.market_anomaly_detector,
            market_insider_activity_tracker=self.market_insider_activity_tracker,
            market_insider_alert_pipeline=self.market_insider_alert_pipeline,
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
            market_portfolio_event_intelligence_hub=self.market_portfolio_event_intelligence_hub,
            market_portfolio_integration_hub=self.market_portfolio_integration_hub,
            market_portfolio_monitor=self.market_portfolio_monitor,
            market_portfolio_performance_analytics=self.market_portfolio_performance_analytics,
            market_portfolio_predictive_aggregator=self.market_portfolio_predictive_aggregator,
            market_portfolio_scenario_simulator=self.market_portfolio_scenario_simulator,
            market_portfolio_strategy_optimizer=self.market_portfolio_strategy_optimizer,
            market_portfolio_stress_reporter=self.market_portfolio_stress_reporter,
            market_portfolio_telegram_command_center=self.market_portfolio_telegram_command_center,
            market_portfolio_telegram_notifier=self.market_portfolio_telegram_notifier,
            market_portfolio_valuation=self.market_portfolio_valuation,
            market_portfolio_visualizer_v2=self.market_portfolio_visualizer_v2,
            market_portfolio_webhook_event_logger=self.market_portfolio_webhook_event_logger,
            market_portfolio_webhook_sync=self.market_portfolio_webhook_sync,
            market_report_generator=self.market_report_generator,
            market_telegram_pipeline=self.market_telegram_pipeline
        )

    def test_analyze_portfolio_insider_risk_success(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_anomaly_score = random.uniform(1.0, 100.0)
        rand_insider_volume = random.randint(1000, 500000)
        
        self.market_anomaly_detector.detect.return_value = {"score": rand_anomaly_score}
        self.market_insider_activity_tracker.get_volume.return_value = rand_insider_volume

        result = self.analyzer.analyze_risk(rand_portfolio_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), rand_portfolio_id)
        self.assertEqual(result.get("anomaly_score"), rand_anomaly_score)
        self.assertEqual(result.get("insider_volume"), rand_insider_volume)
        self.market_anomaly_detector.detect.assert_called_once_with(rand_portfolio_id)
        self.market_insider_activity_tracker.get_volume.assert_called_once_with(rand_portfolio_id)

    def test_stream_parsing_and_risk_computation(self):
        rand_stream_data = ''.join(random.choices(string.ascii_letters + string.digits, k=128)).encode('utf-8')
        mock_stream = io.BytesIO(rand_stream_data)
        
        rand_parsed_key = uuid.uuid4().hex
        self.market_parser.parse_stream.return_value = {rand_parsed_key: random.randint(1, 999)}

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = rand_stream_data
            mock_get.return_value = mock_response

            res = self.analyzer.process_market_stream(mock_stream)
            self.assertIn(rand_parsed_key, res)

    def test_alert_dispatch_on_high_risk(self):
        rand_alert_id = uuid.uuid4().hex
        rand_msg = ''.join(random.choices(string.ascii_letters, k=32))
        
        self.market_portfolio_alert_dispatcher.dispatch.return_value = True

        status = self.analyzer.trigger_alert(rand_alert_id, rand_msg)

        self.assertTrue(status)
        self.market_portfolio_alert_dispatcher.dispatch.assert_called_once_with(rand_alert_id, rand_msg)

    def test_audit_compliance_logging(self):
        rand_audit_uuid = uuid.uuid4().hex
        rand_compliance_status = random.choice([True, False])
        
        self.market_portfolio_audit_compliance_hub.verify.return_value = rand_compliance_status

        result = self.analyzer.audit_compliance(rand_audit_uuid)

        self.assertEqual(result, rand_compliance_status)
        self.market_portfolio_audit_compliance_hub.verify.assert_called_once_with(rand_audit_uuid)

    def test_valuation_and_scenario_simulation(self):
        rand_asset_id = uuid.uuid4().hex
        rand_valuation_val = random.uniform(10.5, 9999.99)
        
        self.market_portfolio_valuation.calculate.return_value = rand_valuation_val
        self.market_portfolio_scenario_simulator.simulate.return_value = {"status": "ok", "value": rand_valuation_val}

        simulation_result = self.analyzer.simulate_market_shock(rand_asset_id)

        self.assertEqual(simulation_result.get("value"), rand_valuation_val)
        self.market_portfolio_valuation.calculate.assert_called_once_with(rand_asset_id)
        self.market_portfolio_scenario_simulator.simulate.assert_called_once_with(rand_asset_id, rand_valuation_val)

if __name__ == '__main__':
    unittest.main()