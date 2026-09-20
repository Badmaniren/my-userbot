import unittest
import os
import uuid
import random
import tempfile
from unittest.mock import patch
from skills.market_portfolio_webhook_sync import sync_portfolio_via_webhook, webhook_sync_pipeline

class TestMarketPortfolioWebhookSyncIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"test_portfolio_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"http://example.com/api/market/{uuid.uuid4().hex}"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))
        self.webhook_url = f"http://localhost/webhook/{uuid.uuid4().hex}"

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('skills.market_portfolio_webhook_sync.requests.post')
    @patch('skills.market_portfolio_alert_dispatcher.send_telegram_notification')
    def test_sync_portfolio_via_webhook_failure_flow(self, mock_telegram_send, mock_requests_post):
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 500
        mock_response.text = f"Internal Server Error {uuid.uuid4().hex}"
        mock_requests_post.return_value = mock_response

        response = sync_portfolio_via_webhook(
            self.webhook_url,
            self.storage_file,
            self.url,
            self.telegram_token,
            self.chat_id
        )

        self.assertEqual(response.status_code, 500)
        mock_telegram_send.assert_called_once()
        called_args = mock_telegram_send.call_args[0]
        self.assertEqual(called_args[0], self.telegram_token)
        self.assertEqual(called_args[1], self.chat_id)
        self.assertIn("Webhook sync failed with status code 500", called_args[2])

    @patch('skills.market_portfolio_webhook_sync.sync_portfolio_via_webhook')
    def test_webhook_sync_pipeline_exception_handling(self, mock_sync_func):
        mock_sync_func.side_effect = Exception(f"Connection timeout {uuid.uuid4().hex}")

        result = webhook_sync_pipeline(
            self.symbol,
            self.url,
            self.telegram_token,
            self.chat_id,
            self.storage_file
        )

        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(self.storage_file))

    @patch('skills.market_portfolio_webhook_sync.requests.post')
    def test_webhook_sync_pipeline_success_flow(self, mock_requests_post):
        expected_json = {"status": "synced", "id": uuid.uuid4().hex}
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_json
        mock_requests_post.return_value = mock_response

        result = webhook_sync_pipeline(
            self.symbol,
            self.url,
            self.telegram_token,
            self.chat_id,
            self.storage_file
        )

        self.assertEqual(result, expected_json)
        self.assertTrue(os.path.exists(self.storage_file))
        mock_requests_post.assert_called_once()

if __name__ == '__main__':
    unittest.main()