import unittest
from unittest.mock import patch
import os
import json
import uuid
import random
import tempfile

from skills.market_portfolio_alert_event_sink import (
    handle_portfolio_alert_event,
    process_incoming_stream,
    route_and_sink_alerts,
    load_sink_stream_data,
    process_event_sink_trigger,
    AlertFilterRouter
)

class TestMarketPortfolioAlertEventSink(unittest.TestCase):

    def setUp(self):
        self.rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.rand_url = f"https://example.com/api/{uuid.uuid4().hex}"
        self.rand_token = uuid.uuid4().hex
        self.rand_chat_id = str(random.randint(100000, 999999))
        self.rand_severity = random.choice(["INFO", "WARNING", "CRITICAL"])
        self.rand_threshold = round(random.uniform(1.0, 100.0), 2)
        self.rand_channels = [random.choice(["telegram", "webhook", "email"])]
        self.rand_alert_id = uuid.uuid4().hex
        
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"storage_{uuid.uuid4().hex}.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("skills.market_portfolio_alert_dispatcher.dispatch_portfolio_alerts")
    def test_handle_portfolio_alert_event(self, mock_dispatch):
        expected_result = {"status": "dispatched", "ref": uuid.uuid4().hex}
        mock_dispatch.return_value = expected_result

        result = handle_portfolio_alert_event(
            self.rand_symbol,
            self.rand_url,
            self.rand_token,
            self.rand_chat_id,
            self.storage_file,
            self.rand_severity,
            self.rand_threshold,
            self.rand_channels
        )

        mock_dispatch.assert_called_once_with(
            self.rand_symbol,
            self.rand_url,
            self.rand_token,
            self.rand_chat_id,
            self.storage_file,
            self.rand_severity,
            self.rand_threshold,
            self.rand_channels
        )
        self.assertEqual(result, expected_result)

    @patch("skills.market_portfolio_alert_dispatcher.process_stream_alert")
    def test_process_incoming_stream(self, mock_process_stream):
        expected_stream_data = {"alert_id": self.rand_alert_id, "processed": True}
        mock_process_stream.return_value = expected_stream_data

        result = process_incoming_stream(self.rand_alert_id)

        mock_process_stream.assert_called_once_with(self.rand_alert_id)
        self.assertEqual(result, expected_stream_data)

    @patch.object(AlertFilterRouter, "route_filtered_alerts")
    def test_route_and_sink_alerts(self, mock_route):
        expected_routing = {"routed": True, "symbol": self.rand_symbol}
        mock_route.return_value = expected_routing

        result = route_and_sink_alerts(
            self.storage_file,
            self.rand_symbol,
            self.rand_url,
            self.rand_token,
            self.rand_chat_id,
            self.rand_severity,
            self.rand_threshold,
            self.rand_channels
        )

        self.assertEqual(result, expected_routing)

    @patch.object(AlertFilterRouter, "load_stream_data")
    def test_load_sink_stream_data(self, mock_load):
        expected_data = {"stream": uuid.uuid4().hex}
        mock_load.return_value = expected_data

        result = load_sink_stream_data(self.storage_file)

        self.assertEqual(result, expected_data)

    @patch("skills.market_portfolio_alert_filter_router.AlertFilterRouter.route_filtered_alerts")
    @patch("skills.market_portfolio_alert_dispatcher.dispatch_portfolio_alerts")
    def test_process_event_sink_trigger_new_file(self, mock_dispatch, mock_route):
        dispatch_mock_response = {"dispatch_id": uuid.uuid4().hex}
        mock_dispatch.return_value = dispatch_mock_response
        mock_route.return_value = True

        self.assertFalse(os.path.exists(self.storage_file))

        result = process_event_sink_trigger(
            self.rand_symbol,
            self.rand_url,
            self.rand_token,
            self.rand_chat_id,
            self.storage_file,
            self.rand_severity,
            self.rand_threshold,
            self.rand_channels
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["symbol"], self.rand_symbol)
        self.assertEqual(result["dispatch_result"], dispatch_mock_response)

        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["symbol"], self.rand_symbol)
            self.assertEqual(data["status"], "processed")

    @patch("skills.market_portfolio_alert_filter_router.AlertFilterRouter.route_filtered_alerts")
    @patch("skills.market_portfolio_alert_dispatcher.dispatch_portfolio_alerts")
    def test_process_event_sink_trigger_existing_file(self, mock_dispatch, mock_route):
        dispatch_mock_response = {"dispatch_id": uuid.uuid4().hex}
        mock_dispatch.return_value = dispatch_mock_response
        mock_route.return_value = True

        initial_data = {"symbol": "OLD_SYM", "extra": uuid.uuid4().hex}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        result = process_event_sink_trigger(
            self.rand_symbol,
            self.rand_url,
            self.rand_token,
            self.rand_chat_id,
            self.storage_file,
            self.rand_severity,
            self.rand_threshold,
            self.rand_channels
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["symbol"], self.rand_symbol)

        with open(self.storage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["symbol"], self.rand_symbol)
            self.assertEqual(data["status"], "processed")
            self.assertEqual(data["extra"], initial_data["extra"])

if __name__ == "__main__":
    unittest.main()