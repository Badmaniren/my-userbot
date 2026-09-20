import unittest
from unittest.mock import patch
import os
import json
import uuid
import random
import tempfile
import io
from skills.market_portfolio_webhook_sync import (
    MarketParser,
    AutonomousSentinel,
    MarketPortfolioIntegrationHub,
    MarketPortfolioWebhookSync,
    start_new,
    send_telegram_notification
)

class TestMarketPortfolioWebhookSync(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex
        self.storage_file = f"test_storage_{self.random_suffix}.json"
        self.webhook_url = f"https://example.com/webhook/{self.random_suffix}"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.price = round(random.uniform(10.0, 1000.0), 2)
        self.url = f"https://market.data/{uuid.uuid4().hex}"
        self.token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.threshold = round(random.uniform(0.1, 5.0), 2)
        self.shift = random.randint(1, 10)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_send_telegram_notification(self):
        result = send_telegram_notification()
        self.assertTrue(result)

    def test_market_parser_fetch_and_parse(self):
        parser = MarketParser(self.storage_file)
        price = parser.fetch_price(self.url)
        prices = parser.parse_html_prices(self.url)
        self.assertEqual(price, 100.0)
        self.assertEqual(prices, [100.0])

    def test_market_parser_load_data_empty(self):
        parser = MarketParser(self.storage_file)
        data = parser.load_data()
        self.assertEqual(data, b"")

    def test_market_parser_load_data_existing(self):
        random_bytes = uuid.uuid4().bytes
        with open(self.storage_file, "wb") as f:
            f.write(random_bytes)
        
        parser = MarketParser(self.storage_file)
        data = parser.load_data()
        self.assertEqual(data, random_bytes)

    def test_autonomous_sentinel_surveillance(self):
        sentinel = AutonomousSentinel(self.storage_file, self.threshold)
        res = sentinel.run_surveillance(self.symbol, self.url, self.token, self.chat_id)
        self.assertTrue(res)

    def test_market_portfolio_integration_hub_pipeline(self):
        hub = MarketPortfolioIntegrationHub(self.storage_file)
        result = hub.run_integrated_pipeline(
            url=self.url,
            symbol=self.symbol,
            shifts=self.shift,
            telegram_token=self.token,
            chat_id=self.chat_id
        )
        self.assertEqual(result["symbol"], self.symbol)
        self.assertEqual(result["price"], 100.0)
        self.assertEqual(result["url"], self.url)
        self.assertEqual(result["token"], self.token)
        self.assertEqual(result["chat_id"], self.chat_id)
        self.assertEqual(result["shift"], self.shift)
        self.assertEqual(result["storage"], self.storage_file)
        self.assertEqual(result["msg"], f"alert_{self.symbol}")

    def test_market_portfolio_integration_hub_with_storage(self):
        initial_data = {self.symbol: self.price}
        with open(self.storage_file, "w") as f:
            json.dump(initial_data, f)

        hub = MarketPortfolioIntegrationHub(self.storage_file)
        result = hub.run_integrated_pipeline(
            url=self.url,
            symbol=self.symbol,
            shifts=self.shift,
            telegram_token=self.token,
            chat_id=self.chat_id
        )
        self.assertEqual(result["price"], self.price)

    def test_start_new_execution(self):
        result = start_new(
            storage_file=self.storage_file,
            url=self.url,
            symbol=self.symbol,
            telegram_token=self.token,
            chat_id=self.chat_id,
            threshold=self.threshold,
            shift=self.shift
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], self.symbol)

    def test_webhook_sync_store_initial_state(self):
        sync = MarketPortfolioWebhookSync(self.storage_file, self.webhook_url)
        sync.store_initial_state(self.symbol, self.price)

        with open(self.storage_file, "r") as f:
            data = json.load(f)
        
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], self.price)

    def test_webhook_sync_trigger_webhook_sync(self):
        sync = MarketPortfolioWebhookSync(self.storage_file, self.webhook_url)
        response = sync.trigger_webhook_sync(self.symbol, self.price)

        expected_response = {
            "status": "success",
            "symbol": self.symbol,
            "price": self.price,
            "webhook_url": self.webhook_url
        }
        self.assertEqual(response, expected_response)

        with open(self.storage_file, "r") as f:
            data = json.load(f)
        self.assertEqual(data.get(self.symbol), self.price)

    def test_webhook_sync_load_data(self):
        sync = MarketPortfolioWebhookSync(self.storage_file, self.webhook_url)
        initial_data = {self.symbol: self.price}
        with open(self.storage_file, "w") as f:
            json.dump(initial_data, f)

        loaded = sync.load_data(self.storage_file)
        self.assertEqual(loaded, initial_data)

    def test_webhook_sync_load_data_nonexistent(self):
        sync = MarketPortfolioWebhookSync(self.storage_file, self.webhook_url)
        non_existent_file = f"nonexistent_{uuid.uuid4().hex}.json"
        loaded = sync.load_data(non_existent_file)
        self.assertEqual(loaded, {})

if __name__ == "__main__":
    unittest.main()