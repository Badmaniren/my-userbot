import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json
import os

from skills.market_portfolio_anomaly_detector import MarketPortfolioAnomalyDetector


class TestMarketPortfolioAnomalyDetector(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.market_parser = MagicMock()
        self.alert_dispatcher = MagicMock()
        self.alert_event_sink = MagicMock()
        self.alert_filter_router = MagicMock()
        self.api_gateway = MagicMock()
        self.audit_notifier = MagicMock()
        self.audit_compliance_hub = MagicMock()
        self.audit_log_exporter = MagicMock()
        self.autonomous_sentinel = MagicMock()
        self.backtest_bridge = MagicMock()
        self.backtester = MagicMock()
        self.collector_agent = MagicMock()
        self.data_exporter = MagicMock()
        self.digest = MagicMock()
        self.event_hub = MagicMock()
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
        self.visualizer_v2 = MagicMock()
        self.webhook_event_logger = MagicMock()
        self.webhook_sync = MagicMock()
        self.market_report_generator = MagicMock()
        self.market_telegram_pipeline = MagicMock()

        self.detector = MarketPortfolioAnomalyDetector(
            db_storage=self.db_storage,
            market_parser=self.market_parser,
            market_portfolio_alert_dispatcher=self.alert_dispatcher,
            market_portfolio_alert_event_sink=self.alert_event_sink,
            market_portfolio_alert_filter_router=self.alert_filter_router,
            market_portfolio_api_gateway=self.api_gateway,
            market_portfolio_audit_alert_notifier=self.audit_notifier,
            market_portfolio_audit_compliance_hub=self.audit_compliance_hub,
            market_portfolio_audit_log_exporter=self.audit_log_exporter,
            market_portfolio_autonomous_sentinel=self.autonomous_sentinel,
            market_portfolio_backtest_evaluator_bridge=self.backtest_bridge,
            market_portfolio_backtester=self.backtester,
            market_portfolio_collector_agent=self.collector_agent,
            market_portfolio_data_exporter=self.data_exporter,
            market_portfolio_digest=self.digest,
            market_portfolio_event_intelligence_hub=self.event_hub,
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
            market_portfolio_visualizer_v2=self.visualizer_v2,
            market_portfolio_webhook_event_logger=self.webhook_event_logger,
            market_portfolio_webhook_sync=self.webhook_sync,
            market_report_generator=self.market_report_generator,
            market_telegram_pipeline=self.market_telegram_pipeline
        )

    def test_detect_portfolio_anomaly_success(self):
        portfolio_id = str(uuid.uuid4())
        transaction_id = str(uuid.uuid4())
        anomaly_score = random.uniform(85.0, 99.9)
        random_bytes = ''.join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')

        self.db_storage.fetch_portfolio.return_value = {
            "portfolio_id": portfolio_id,
            "transaction_id": transaction_id,
            "amount": random.randint(100000, 9999999)
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.content = random_bytes
            mock_post.return_value.json.return_value = {"anomaly_score": anomaly_score, "status": "critical"}

            result = self.detector.detect_anomaly(portfolio_id)

            self.assertIn("anomaly_detected", result)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["score"], anomaly_score)
            self.db_storage.fetch_portfolio.assert_called_once_with(portfolio_id)
            self.alert_dispatcher.dispatch.assert_called()

    def test_stream_anomaly_with_io_buffer(self):
        stream_token = uuid.uuid4().hex
        garbage_payload = io.BytesIO(os.urandom(128) if 'os' in globals() else bytes(random.getrandbits(8) for _ in range(128)))

        with patch('skills.market_portfolio_anomaly_detector.io.BytesIO', return_value=garbage_payload):
            self.collector_agent.stream.return_value = garbage_payload

            evaluated = self.detector.process_stream_data(stream_token)
            self.assertTrue(evaluated)
            self.collector_agent.stream.assert_called_once_with(stream_token)

    def test_dispatch_alert_routing(self):
        alert_id = str(uuid.uuid4())
        route_target = ''.join(random.choices(string.ascii_lowercase, k=10))

        self.alert_filter_router.route.return_value = route_target

        alert_payload = {
            "alert_id": alert_id,
            "severity": random.choice(["HIGH", "CRITICAL", "EXTREME"]),
            "msg": uuid.uuid4().hex
        }

        response = self.detector.route_alert(alert_payload)

        self.assertEqual(response["target"], route_target)
        self.assertEqual(response["alert_id"], alert_id)
        self.alert_filter_router.route.assert_called_once_with(alert_payload)
        self.alert_event_sink.sink.assert_called_once()

    def test_audit_compliance_trigger(self):
        audit_tag = uuid.uuid4().hex
        compliance_status = random.choice([True, False])

        self.audit_compliance_hub.verify.return_value = compliance_status

        check_result = self.detector.audit_portfolio_state(audit_tag)

        self.assertEqual(check_result["compliant"], compliance_status)
        self.assertEqual(check_result["tag"], audit_tag)
        self.audit_compliance_hub.verify.assert_called_once_with(audit_tag)
        self.audit_notifier.notify.assert_called()

if __name__ == '__main__':
    unittest.main()