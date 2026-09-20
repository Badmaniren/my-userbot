import unittest
from unittest.mock import patch
import uuid
import random
import requests
from skills.market_portfolio_webhook_sync import sync_portfolio_via_webhook, webhook_sync_pipeline

class TestMarketPortfolioWebhookSync(unittest.TestCase):

    def test_sync_portfolio_via_webhook_success(self):
        rand_webhook = f"http://{uuid.uuid4().hex}.local/webhook"
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_url = f"http://{uuid.uuid4().hex}.com"
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(10000, 99999))
        rand_summary = {uuid.uuid4().hex: random.uniform(10.0, 1000.0)}

        with patch('skills.market_portfolio_webhook_sync.MarketPortfolioAPIGateway') as mock_gateway_cls, \
             patch('requests.post') as mock_post, \
             patch('skills.market_portfolio_webhook_sync.send_telegram_notification') as mock_send_tg:

            mock_gateway_instance = mock_gateway_cls.return_value
            mock_gateway_instance.export_portfolio_summary.return_value = rand_summary

            mock_response = mock_post.return_value
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "success", "data": rand_summary}

            result = sync_portfolio_via_webhook(rand_webhook, rand_storage, rand_url, rand_token, rand_chat)

            mock_gateway_cls.assert_called_once_with(rand_storage)
            mock_gateway_instance.export_portfolio_summary.assert_called_once_with(rand_url)
            mock_post.assert_called_once_with(rand_webhook, json=rand_summary)
            mock_send_tg.assert_not_called()
            self.assertEqual(result, {"status": "success", "data": rand_summary})

    def test_sync_portfolio_via_webhook_failure(self):
        rand_webhook = f"http://{uuid.uuid4().hex}.local/webhook"
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_url = f"http://{uuid.uuid4().hex}.com"
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(10000, 99999))
        rand_summary = {uuid.uuid4().hex: random.uniform(1.0, 50.0)}
        rand_status = random.choice([400, 500, 502, 503])
        rand_text = f"Error_{uuid.uuid4().hex}"

        with patch('skills.market_portfolio_webhook_sync.MarketPortfolioAPIGateway') as mock_gateway_cls, \
             patch('requests.post') as mock_post, \
             patch('skills.market_portfolio_webhook_sync.send_telegram_notification') as mock_send_tg:

            mock_gateway_instance = mock_gateway_cls.return_value
            mock_gateway_instance.export_portfolio_summary.return_value = rand_summary

            mock_response = mock_post.return_value
            mock_response.status_code = rand_status
            mock_response.text = rand_text

            result = sync_portfolio_via_webhook(rand_webhook, rand_storage, rand_url, rand_token, rand_chat)

            mock_gateway_cls.assert_called_once_with(rand_storage)
            mock_gateway_instance.export_portfolio_summary.assert_called_once_with(rand_url)
            mock_post.assert_called_once_with(rand_webhook, json=rand_summary)

            expected_msg = f"Webhook sync failed with status code {rand_status}: {rand_text}"
            mock_send_tg.assert_called_once_with(rand_token, rand_chat, expected_msg)
            self.assertEqual(result, mock_response)

    def test_webhook_sync_pipeline_success(self):
        rand_symbol = uuid.uuid4().hex[:6].upper()
        rand_url = f"http://{uuid.uuid4().hex}.net"
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(100000, 999999))
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_expected_json = {uuid.uuid4().hex: random.randint(100, 500)}

        with patch('skills.market_portfolio_webhook_sync.MarketPortfolioAPIGateway') as mock_gateway_cls, \
             patch('skills.market_portfolio_webhook_sync.sync_portfolio_via_webhook') as mock_sync:

            mock_gateway_instance = mock_gateway_cls.return_value
            mock_sync.return_value = rand_expected_json

            result = webhook_sync_pipeline(rand_symbol, rand_url, rand_token, rand_chat, rand_storage)

            mock_gateway_cls.assert_called_once_with(rand_storage)
            mock_gateway_instance.add_or_update_position.assert_called_once_with(rand_symbol, 1.0, 100.0)
            mock_sync.assert_called_once_with("http://localhost/webhook", rand_storage, rand_url, rand_token, rand_chat)
            self.assertEqual(result, rand_expected_json)

    def test_webhook_sync_pipeline_exception_fallback(self):
        rand_symbol = uuid.uuid4().hex[:6].upper()
        rand_url = f"http://{uuid.uuid4().hex}.net"
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(100000, 999999))
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_summary = {uuid.uuid4().hex: random.random()}

        with patch('skills.market_portfolio_webhook_sync.MarketPortfolioAPIGateway') as mock_gateway_cls, \
             patch('skills.market_portfolio_webhook_sync.sync_portfolio_via_webhook') as mock_sync:

            mock_gateway_instance = mock_gateway_cls.return_value
            mock_sync.side_effect = Exception(uuid.uuid4().hex)
            mock_gateway_instance.export_portfolio_summary.return_value = rand_summary

            result = webhook_sync_pipeline(rand_symbol, rand_url, rand_token, rand_chat, rand_storage)

            mock_gateway_cls.assert_called_once_with(rand_storage)
            mock_gateway_instance.add_or_update_position.assert_called_once_with(rand_symbol, 1.0, 100.0)
            mock_sync.assert_called_once()
            mock_gateway_instance.export_portfolio_summary.assert_called_once_with(rand_url)
            self.assertEqual(result, rand_summary)

if __name__ == '__main__':
    unittest.main()