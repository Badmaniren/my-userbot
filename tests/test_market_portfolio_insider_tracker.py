import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import requests

from skills.market_portfolio_insider_tracker import (
    InsiderTrackerEngine,
    InsiderTrackerException
)

class TestMarketPortfolioInsiderTracker(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
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

        self.engine = InsiderTrackerEngine(
            db_storage=self.db_storage,
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

    def test_collect_and_process_insider_signals(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_insider = ''.join(random.choices(string.ascii_letters, k=10))
        rand_volume = random.randint(1000, 999999)
        rand_tx_id = uuid.uuid4().hex

        parsed_data = {
            "symbol": rand_symbol,
            "insider": rand_insider,
            "volume": rand_volume,
            "tx_id": rand_tx_id
        }
        self.market_parser.extract_insider_trades.return_value = [parsed_data]

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = io.BytesIO(uuid.uuid4().bytes).read()
            mock_get.return_value = mock_response

            result = self.engine.track_market_insiders()

            self.assertTrue(result)
            self.db_storage.save_transaction.assert_called_once()
            args, _ = self.db_storage.save_transaction.call_args
            self.assertEqual(args[0]["tx_id"], rand_tx_id)
            self.assertEqual(args[0]["symbol"], rand_symbol)
            self.market_portfolio_alert_dispatcher.dispatch.assert_called_once()

    def test_alert_filter_router_integration(self):
        rand_event_id = uuid.uuid4().hex
        rand_priority = random.choice(["HIGH", "CRITICAL", "MODERATE"])

        event_payload = {
            "event_id": rand_event_id,
            "priority": rand_priority,
            "data": uuid.uuid4().hex
        }

        self.market_portfolio_alert_filter_router.route_event.return_value = True

        response = self.engine.process_alert_event(event_payload)

        self.assertTrue(response)
        self.market_portfolio_alert_filter_router.route_event.assert_called_once_with(event_payload)
        self.market_portfolio_alert_event_sink.log_event.assert_called_once()

    def test_parser_failure_handling(self):
        rand_url = f"https://{uuid.uuid4().hex}.market/api/insiders"
        self.market_parser.extract_insider_trades.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(InsiderTrackerException):
            self.engine.force_sync_from_url(rand_url)

        self.market_portfolio_audit_alert_notifier.notify_error.assert_called_once()

    def test_predictive_aggregator_workflow(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_score = random.uniform(0.1, 0.99)

        self.market_portfolio_predictive_aggregator.calculate_alpha.return_value = {
            "portfolio_id": rand_portfolio_id,
            "alpha_score": rand_score
        }

        metrics = self.engine.evaluate_predictive_alpha(rand_portfolio_id)

        self.assertEqual(metrics["portfolio_id"], rand_portfolio_id)
        self.assertEqual(metrics["alpha_score"], rand_score)
        self.market_portfolio_predictive_aggregator.calculate_alpha.assert_called_once_with(rand_portfolio_id)

    def test_telegram_pipeline_notification(self):
        rand_chat_id = str(random.randint(100000, 999999))
        rand_msg = uuid.uuid4().hex

        self.engine.send_telegram_insider_alert(rand_chat_id, rand_msg)

        self.market_telegram_pipeline.send_message.assert_called_once_with(rand_chat_id, rand_msg)

    def test_webhook_event_logger_sync(self):
        rand_webhook_url = f"https://webhook.{uuid.uuid4().hex}.io/endpoint"
        rand_payload = {"token": uuid.uuid4().hex}

        with patch('requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 201
            mock_post.return_value = mock_resp

            self.engine.dispatch_webhook_sync(rand_webhook_url, rand_payload)

            mock_post.assert_called_once_with(rand_webhook_url, json=rand_payload, timeout=10)
            self.market_portfolio_webhook_event_logger.record.assert_called_once()

if __name__ == '__main__':
    unittest.main()