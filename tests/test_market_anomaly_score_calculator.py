import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
import requests
from bs4 import BeautifulSoup

from skills.market_anomaly_score_calculator import MarketAnomalyScoreCalculator

class TestMarketAnomalyScoreCalculator(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_tool_1 = MagicMock()
        self.extractor_tool_2 = MagicMock()
        self.market_insider_activity_tracker = MagicMock()
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

        self.calculator = MarketAnomalyScoreCalculator(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_tool_1,
            extractor_tool_1790102839=self.extractor_tool_2,
            market_insider_activity_tracker=self.market_insider_activity_tracker,
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

    def test_calculate_anomaly_score_success(self):
        random_asset_id = uuid.uuid4().hex
        random_score = round(random.uniform(1.0, 100.0), 4)
        random_insider_data = {uuid.uuid4().hex: random.randint(10, 500)}

        self.market_insider_activity_tracker.get_activity.return_value = random_insider_data
        self.extractor_tool_1.extract.return_value = random_score

        result = self.calculator.calculate_score(random_asset_id)

        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)
        self.market_insider_activity_tracker.get_activity.assert_called_once_with(random_asset_id)
        self.extractor_tool_1.extract.assert_called()

    def test_market_parser_integration_with_stream(self):
        random_html_tag = uuid.uuid4().hex
        random_bytes = f"<html><body><div id='{random_html_tag}'>{random.randint(1000, 9999)}</div></body></html>".encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)

        self.market_parser.parse_stream.return_value = BeautifulSoup(mock_stream.read(), 'html.parser')

        parsed_data = self.calculator.process_market_stream(mock_stream)

        found_element = parsed_data.find(id=random_html_tag)
        self.assertIsNotNone(found_element)
        self.assertEqual(found_element.text, str(self.market_parser.parse_stream.return_value.find(id=random_html_tag).text))

    def test_webhook_event_logging_on_anomaly(self):
        random_event_id = uuid.uuid4().hex
        random_url = f"https://{uuid.uuid4().hex}.com/api/v1/webhook"
        random_payload = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "received", "id": random_event_id}
            mock_post.return_value = mock_response

            self.market_portfolio_webhook_event_logger.log_event.return_value = True

            status = self.calculator.dispatch_anomaly_webhook(random_url, random_payload)

            self.assertTrue(status)
            self.market_portfolio_webhook_event_logger.log_event.assert_called_once()

    def test_autonomous_sentinel_alert_trigger(self):
        random_threshold = random.uniform(50.0, 99.9)
        random_alert_msg = "".join(random.choices(string.ascii_letters, k=15))

        self.market_portfolio_autonomous_sentinel.check_threshold.return_value = (True, random_alert_msg)

        triggered, msg = self.calculator.evaluate_sentinel(random_threshold)

        self.assertTrue(triggered)
        self.assertEqual(msg, random_alert_msg)
        self.market_portfolio_autonomous_sentinel.check_threshold.assert_called_once_with(random_threshold)

    def test_audit_compliance_logging(self):
        random_audit_id = uuid.uuid4().hex
        random_user = uuid.uuid4().hex

        self.market_portfolio_audit_compliance_hub.record_audit.return_value = {
            "audit_id": random_audit_id,
            "status": "logged"
        }

        audit_result = self.calculator.audit_action(random_audit_id, random_user)

        self.assertEqual(audit_result["audit_id"], random_audit_id)
        self.assertEqual(audit_result["status"], "logged")
        self.market_portfolio_audit_compliance_hub.record_audit.assert_called_once_with(random_audit_id, random_user)