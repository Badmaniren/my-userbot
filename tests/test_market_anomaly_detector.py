import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
import json

from skills.market_anomaly_detector import MarketAnomalyDetector


class TestMarketAnomalyDetector(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_1 = MagicMock()
        self.extractor_2 = MagicMock()
        self.extractor_3 = MagicMock()
        self.insider_tracker = MagicMock()
        self.market_parser = MagicMock()
        self.alert_dispatcher = MagicMock()
        self.alert_event_sink = MagicMock()
        self.alert_filter_router = MagicMock()
        self.api_gateway = MagicMock()
        self.audit_notifier = MagicMock()
        self.audit_compliance = MagicMock()
        self.audit_log_exporter = MagicMock()
        self.autonomous_sentinel = MagicMock()
        self.backtest_evaluator = MagicMock()
        self.backtester = MagicMock()
        self.collector_agent = MagicMock()
        self.data_exporter = MagicMock()
        self.digest = MagicMock()
        self.event_intelligence = MagicMock()
        self.integration_hub = MagicMock()
        self.monitor = MagicMock()
        self.performance_analytics = MagicMock()
        self.predictive_aggregator = MagicMock()
        self.scenario_simulator = MagicMock()
        self.strategy_optimizer = MagicMock()
        self.stress_reporter = MagicMock()
        self.telegram_command_center = MagicMock()
        self.telegram_notifier = MagicMock()
        self.valuation = MagicMock()
        self.visualizer = MagicMock()
        self.webhook_logger = MagicMock()
        self.webhook_sync = MagicMock()
        self.report_generator = MagicMock()
        self.telegram_pipeline = MagicMock()

        self.detector = MarketAnomalyDetector(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_1,
            extractor_tool_1790102839=self.extractor_2,
            extractor_tool_1790262909=self.extractor_3,
            market_insider_activity_tracker=self.insider_tracker,
            market_parser=self.market_parser,
            market_portfolio_alert_dispatcher=self.alert_dispatcher,
            market_portfolio_alert_event_sink=self.alert_event_sink,
            market_portfolio_alert_filter_router=self.alert_filter_router,
            market_portfolio_api_gateway=self.api_gateway,
            market_portfolio_audit_alert_notifier=self.audit_notifier,
            market_portfolio_audit_compliance_hub=self.audit_compliance,
            market_portfolio_audit_log_exporter=self.audit_log_exporter,
            market_portfolio_autonomous_sentinel=self.autonomous_sentinel,
            market_portfolio_backtest_evaluator_bridge=self.backtest_evaluator,
            market_portfolio_backtester=self.backtester,
            market_portfolio_collector_agent=self.collector_agent,
            market_portfolio_data_exporter=self.data_exporter,
            market_portfolio_digest=self.digest,
            market_portfolio_event_intelligence_hub=self.event_intelligence,
            market_portfolio_integration_hub=self.integration_hub,
            market_portfolio_monitor=self.monitor,
            market_portfolio_performance_analytics=self.performance_analytics,
            market_portfolio_predictive_aggregator=self.predictive_aggregator,
            market_portfolio_scenario_simulator=self.scenario_simulator,
            market_portfolio_strategy_optimizer=self.strategy_optimizer,
            market_portfolio_stress_reporter=self.stress_reporter,
            market_portfolio_telegram_command_center=self.telegram_command_center,
            market_portfolio_telegram_notifier=self.telegram_notifier,
            market_portfolio_valuation=self.valuation,
            market_portfolio_visualizer_v2=self.visualizer,
            market_portfolio_webhook_event_logger=self.webhook_logger,
            market_portfolio_webhook_sync=self.webhook_sync,
            market_report_generator=self.report_generator,
            market_telegram_pipeline=self.telegram_pipeline
        )

    def test_detect_anomaly_success_flow(self):
        random_ticker = ''.join(random.choices(string.ascii_uppercase, k=5))
        random_anomaly_id = uuid.uuid4().hex
        random_volume = random.randint(10000, 999999)

        self.market_parser.parse.return_value = {
            "ticker": random_ticker,
            "volume": random_volume,
            "anomaly_id": random_anomaly_id
        }

        with patch('requests.get') as mock_get:
            random_url = f"https://{uuid.uuid4().hex}.market/api/v1/feed"
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = io.BytesIO(json.dumps({"status": "active", "id": random_anomaly_id}).encode('utf-8')).read()
            mock_get.return_value = mock_response

            result = self.detector.detect_anomaly(random_ticker)

            self.assertIsNotNone(result)
            self.assertEqual(result.get("ticker"), random_ticker)
            self.assertEqual(result.get("anomaly_id"), random_anomaly_id)
            self.db_storage.save.assert_called_once()
            self.alert_dispatcher.dispatch.assert_called_once()

    def test_anomaly_detector_with_empty_stream(self):
        random_stream_id = uuid.uuid4().hex
        random_bytes = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)

        self.collector_agent.collect.return_value = random_bytes

        with patch('bs4.BeautifulSoup') as mock_bs:
            mock_soup = MagicMock()
            mock_soup.find.return_value = None
            mock_bs.return_value = mock_soup

            anomaly_found = self.detector.evaluate_stream(random_stream_id)

            self.assertFalse(anomaly_found)
            self.autonomous_sentinel.trigger_fallback.assert_not_called()

    def test_insider_activity_correlation(self):
        random_insider_id = uuid.uuid4().hex
        random_score = random.uniform(0.1, 0.99)

        self.insider_tracker.get_activity.return_value = {
            "insider_id": random_insider_id,
            "score": random_score,
            "flagged": True
        }

        self.predictive_aggregator.aggregate.return_value = {
            "risk_level": "CRITICAL",
            "confidence": random_score
        }

        report = self.detector.correlate_insider_activity(random_insider_id)

        self.assertEqual(report["insider_id"], random_insider_id)
        self.assertEqual(report["risk_level"], "CRITICAL")
        self.telegram_notifier.send_alert.assert_called_once()

    def test_stress_reporter_integration(self):
        random_scenario_name = f"scenario_{uuid.uuid4().hex[:8]}"
        random_loss_value = random.uniform(1000.0, 50000.0)

        self.stress_reporter.simulate_stress.return_value = {
            "scenario": random_scenario_name,
            "estimated_loss": random_loss_value
        }

        self.scenario_simulator.run.return_value = True

        output = self.detector.run_stress_test(random_scenario_name)

        self.assertEqual(output["scenario"], random_scenario_name)
        self.assertEqual(output["estimated_loss"], random_loss_value)
        self.audit_compliance.verify.assert_called_once()

    def test_webhook_event_logging(self):
        random_event_type = f"event_{uuid.uuid4().hex[:6]}"
        random_payload = {"uuid": uuid.uuid4().hex, "data": random.randint(1, 100)}

        self.webhook_logger.log_event.return_value = True

        status = self.detector.process_webhook_event(random_event_type, random_payload)

        self.assertTrue(status)
        self.webhook_logger.log_event.assert_called_once_with(random_event_type, random_payload)
        self.webhook_sync.sync.assert_called_once()


if __name__ == '__main__':
    unittest.main()