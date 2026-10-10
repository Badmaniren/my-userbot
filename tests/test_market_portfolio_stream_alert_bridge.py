import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from skills.market_portfolio_stream_alert_bridge import (
    process_stream_and_dispatch,
    evaluate_stream_anomaly_bridge
)


class TestMarketPortfolioStreamAlertBridge(unittest.TestCase):

    def setUp(self):
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_url = f"https://{uuid.uuid4().hex}.com/stream"
        self.random_token = uuid.uuid4().hex
        self.random_chat_id = str(random.randint(100000, 99999999))
        self.random_storage = f"/tmp/{uuid.uuid4().hex}.json"
        self.random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.random_threshold = round(random.uniform(1.0, 15.5), 2)
        self.random_channel = random.choice(["telegram", "webhook", "email"])
        self.random_payload_key = uuid.uuid4().hex
        self.random_payload_val = random.randint(100, 9999)

    def test_process_stream_and_dispatch_success(self):
        input_payload = {self.random_payload_key: self.random_payload_val, "symbol": self.random_symbol}
        output_path = f"/tmp/{uuid.uuid4().hex}.tmp"
        
        mock_stream_result = {
            "status": "success",
            "data": input_payload,
            "anomaly_detected": True,
            "stream_id": uuid.uuid4().hex
        }

        with patch('skills.market_portfolio_stream_alert_bridge.market_portfolio_realtime_stream_ingestor') as mock_ingestor, \
             patch('skills.market_portfolio_stream_alert_bridge.dispatch_portfolio_alerts') as mock_dispatch:
            
            mock_ingestor.return_value = mock_stream_result
            mock_dispatch.return_value = {"dispatched": True, "target": self.random_chat_id}

            result = process_stream_and_dispatch(
                payload=input_payload,
                output_path=output_path,
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_storage,
                severity_level=self.random_severity,
                min_threshold=self.random_threshold,
                channels=[self.random_channel]
            )

            mock_ingestor.assert_called_once_with(input_payload, output_path)
            mock_dispatch.assert_called_once()
            
            called_args = mock_dispatch.call_args[0]
            self.assertEqual(called_args[0], self.random_symbol)
            self.assertEqual(called_args[1], self.random_url)
            self.assertEqual(called_args[2], self.random_token)
            self.assertEqual(called_args[3], self.random_chat_id)
            self.assertEqual(called_args[4], self.random_storage)
            self.assertEqual(called_args[5], self.random_severity)
            self.assertEqual(called_args[6], self.random_threshold)
            self.assertEqual(called_args[7], [self.random_channel])

            self.assertEqual(result["stream_processing"], mock_stream_result)
            self.assertEqual(result["alert_dispatch_status"], {"dispatched": True, "target": self.random_chat_id})

    def test_evaluate_stream_anomaly_bridge_start_new(self):
        random_context_key = uuid.uuid4().hex
        random_context_val = uuid.uuid4().hex
        context = {random_context_key: random_context_val}
        stream_source = io.BytesIO(uuid.uuid4().bytes)

        expected_start_result = {
            "validation": "PASSED",
            "source_id": uuid.uuid4().hex,
            "context_echo": random_context_val
        }

        with patch('skills.market_portfolio_stream_alert_bridge.start_new') as mock_start_new, \
             patch('skills.market_portfolio_stream_alert_bridge.send_telegram_notification') as mock_notify:
            
            mock_start_new.return_value = expected_start_result
            mock_notify.return_value = True

            result = evaluate_stream_anomaly_bridge(
                context=context,
                stream_source=stream_source,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                alert_message_template=uuid.uuid4().hex
            )

            mock_start_new.assert_called_once_with(context, stream_source)
            mock_notify.assert_called_once()
            
            notification_call_args = mock_notify.call_args[0]
            self.assertEqual(notification_call_args[0], self.random_token)
            self.assertEqual(notification_call_args[1], self.random_chat_id)
            self.assertIn(expected_start_result["source_id"], notification_call_args[2])

            self.assertEqual(result, expected_start_result)

    def test_process_stream_and_dispatch_no_anomaly(self):
        input_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        output_path = f"/tmp/{uuid.uuid4().hex}.tmp"
        
        mock_stream_result = {
            "status": "normal",
            "data": input_payload,
            "anomaly_detected": False
        }

        with patch('skills.market_portfolio_stream_alert_bridge.market_portfolio_realtime_stream_ingestor') as mock_ingestor, \
             patch('skills.market_portfolio_stream_alert_bridge.dispatch_portfolio_alerts') as mock_dispatch:
            
            mock_ingestor.return_value = mock_stream_result

            result = process_stream_and_dispatch(
                payload=input_payload,
                output_path=output_path,
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_storage,
                severity_level=self.random_severity,
                min_threshold=self.random_threshold,
                channels=[self.random_channel]
            )

            mock_ingestor.assert_called_once_with(input_payload, output_path)
            mock_dispatch.assert_not_called()
            self.assertFalse(result["alert_dispatched"])


if __name__ == '__main__':
    unittest.main()