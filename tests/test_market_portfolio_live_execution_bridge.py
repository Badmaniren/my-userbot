import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json
import os

from skills.market_portfolio_live_execution_bridge import MarketPortfolioLiveExecutionBridge

class TestMarketPortfolioLiveExecutionBridge(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.webhook_url = f"https://{uuid.uuid4().hex}.com/webhook"
        self.telegram_token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.bridge = MarketPortfolioLiveExecutionBridge(self.storage_file, self.webhook_url)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_init_sets_attributes(self):
        rand_storage = f"{uuid.uuid4().hex}.db"
        rand_webhook = f"https://{uuid.uuid4().hex}.net/api"
        bridge_instance = MarketPortfolioLiveExecutionBridge(rand_storage, rand_webhook)
        self.assertEqual(bridge_instance.storage_file, rand_storage)
        self.assertEqual(bridge_instance.webhook_url, rand_webhook)

    def test_execute_live_order_success(self):
        target_price = round(random.uniform(10.0, 1000.0), 2)
        allocated_capital = round(random.uniform(100.0, 5000.0), 2)
        expected_response = {
            "status": "executed",
            "order_id": uuid.uuid4().hex,
            "symbol": self.symbol,
            "price": target_price,
            "capital": allocated_capital
        }

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = expected_response
            mock_post.return_value = mock_response

            result = self.bridge.execute_live_order(self.symbol, target_price, allocated_capital)

            mock_post.assert_called_once()
            self.assertEqual(result, expected_response)
            self.assertEqual(result["symbol"], self.symbol)
            self.assertEqual(result["price"], target_price)

    def test_execute_live_order_network_failure(self):
        target_price = round(random.uniform(1.0, 50.0), 2)
        allocated_capital = round(random.uniform(50.0, 500.0), 2)

        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception(f"Connection timeout: {uuid.uuid4().hex}")

            result = self.bridge.execute_live_order(self.symbol, target_price, allocated_capital)

            self.assertIn("error", result)
            self.assertEqual(result["symbol"], self.symbol)
            self.assertEqual(result["status"], "failed")

    def test_sync_strategy_with_execution_stream(self):
        random_data_chunk = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        mock_file_stream = io.BytesIO(random_data_chunk)

        mock_storage_payload = {
            self.symbol: {
                "last_price": round(random.uniform(100.0, 999.0), 2),
                "signal": random.choice(["BUY", "SELL", "HOLD"])
            }
        }

        with patch('builtins.open', return_value=mock_file_stream):
            with patch('json.load', return_value=mock_storage_payload):
                sync_result = self.bridge.sync_strategy_with_execution_stream(self.symbol)
                self.assertIsInstance(sync_result, dict)
                self.assertIn(self.symbol, sync_result)
                self.assertEqual(sync_result[self.symbol]["signal"], mock_storage_payload[self.symbol]["signal"])

    def test_dispatch_live_alert_notification(self):
        alert_message = f"ALERT: Strategy triggered for {self.symbol} with hash {uuid.uuid4().hex}"

        with patch('requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_post.return_value = mock_resp

            dispatch_result = self.bridge.dispatch_live_alert(self.telegram_token, self.chat_id, alert_message)

            mock_post.assert_called_once()
            self.assertTrue(dispatch_result)

            args, kwargs = mock_post.call_args
            called_url = args[0]
            self.assertIn(self.telegram_token, called_url)
            json_body = kwargs.get('json', {})
            self.assertEqual(json_body.get('chat_id'), self.chat_id)
            self.assertEqual(json_body.get('text'), alert_message)

    def test_evaluate_and_execute_bridge_pipeline(self):
        mock_evaluation_result = {
            "symbol": self.symbol,
            "action": "BUY",
            "suggested_price": round(random.uniform(50.0, 150.0), 2),
            "allocation": round(random.uniform(1000.0, 5000.0), 2),
            "execution_allowed": True
        }

        with patch.object(self.bridge, 'sync_strategy_with_execution_stream', return_value={self.symbol: mock_evaluation_result}) as mock_sync:
            with patch.object(self.bridge, 'execute_live_order', return_value={"status": "success", "id": uuid.uuid4().hex}) as mock_exec:
                with patch.object(self.bridge, 'dispatch_live_alert', return_value=True) as mock_alert:

                    pipeline_summary = self.bridge.run_bridge_pipeline(self.symbol, self.telegram_token, self.chat_id)

                    mock_sync.assert_called_once_with(self.symbol)
                    mock_exec.assert_called_once()
                    mock_alert.assert_called_once()
                    self.assertIsInstance(pipeline_summary, dict)
                    self.assertEqual(pipeline_summary.get("symbol"), self.symbol)
                    self.assertEqual(pipeline_summary.get("pipeline_status"), "completed")

if __name__ == '__main__':
    unittest.main()