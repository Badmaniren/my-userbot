import unittest
from unittest.mock import patch
import os
import json
import uuid
import random
import io
from skills.market_portfolio_webhook_sync import MarketPortfolioWebhookSync

class TestMarketPortfolioWebhookSync(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_store_{uuid.uuid4().hex}.json"
        self.webhook_url = f"https://{uuid.uuid4().hex}.com/webhook"
        self.symbol = uuid.uuid4().hex[:6].upper()
        self.price = round(random.uniform(10.0, 1000.0), 2)
        self.sync_instance = MarketPortfolioWebhookSync(self.storage_file, self.webhook_url)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_store_initial_state_creates_file_and_data(self):
        self.sync_instance.store_initial_state(self.symbol, self.price)
        self.assertTrue(os.path.exists(self.storage_file))
        
        with open(self.storage_file, "r") as f:
            data = json.load(f)
        
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], self.price)

    def test_store_initial_state_updates_existing_data(self):
        initial_price = self.price
        updated_price = round(initial_price + random.uniform(1.0, 50.0), 2)
        
        self.sync_instance.store_initial_state(self.symbol, initial_price)
        self.sync_instance.store_initial_state(self.symbol, updated_price)
        
        with open(self.storage_file, "r") as f:
            data = json.load(f)
            
        self.assertEqual(data[self.symbol], updated_price)

    def test_trigger_webhook_sync_returns_expected_structure(self):
        result = self.sync_instance.trigger_webhook_sync(self.symbol, self.price)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("symbol"), self.symbol)
        self.assertEqual(result.get("price"), self.price)
        self.assertEqual(result.get("webhook_url"), self.webhook_url)

    def test_trigger_webhook_sync_persists_data(self):
        self.sync_instance.trigger_webhook_sync(self.symbol, self.price)
        
        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r") as f:
            data = json.load(f)
            
        self.assertEqual(data.get(self.symbol), self.price)

    def test_load_data_returns_empty_dict_when_file_missing(self):
        missing_file = f"missing_{uuid.uuid4().hex}.json"
        data = self.sync_instance.load_data(missing_file)
        self.assertEqual(data, {})

    def test_load_data_returns_correct_content(self):
        payload = {self.symbol: self.price}
        with open(self.storage_file, "w") as f:
            json.dump(payload, f)
            
        loaded_data = self.sync_instance.load_data(self.storage_file)
        self.assertEqual(loaded_data, payload)

    def test_load_data_with_mocked_file_read(self):
        random_bytes = json.dumps({self.symbol: self.price}).encode("utf-8")
        mock_file = io.BytesIO(random_bytes)
        
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", return_value=mock_file):
            
            loaded_data = self.sync_instance.load_data(self.storage_file)
            self.assertEqual(loaded_data.get(self.symbol), self.price)

if __name__ == "__main__":
    unittest.main()