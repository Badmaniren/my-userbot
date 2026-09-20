import unittest
import os
import uuid
import tempfile
from unittest.mock import patch
from skills.market_threshold_pipeline import run_threshold_pipeline, check_market_threshold
from skills.market_parser import MarketParser

class TestMarketThresholdPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_market_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://example.com/market/{uuid.uuid4().hex}"
        self.threshold = float(uuid.uuid4().int % 1000) + 50.0
        self.current_price = self.threshold + 25.0

    def tearDown(self):
        self.test_dir.cleanup()

    @patch('skills.market_parser.MarketParser.fetch_price')
    def test_pipeline_integration_without_telegram(self, mock_fetch_price):
        mock_fetch_price.return_value = self.current_price

        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(self.symbol, self.current_price)

        triggered = run_threshold_pipeline(
            symbol=self.symbol,
            url=self.url,
            storage_file=self.storage_file,
            threshold=self.threshold,
            telegram_token=None,
            chat_id=None
        )

        self.assertTrue(triggered)

    @patch('skills.market_parser.MarketParser.fetch_price')
    @patch('skills.market_threshold_pipeline.send_telegram_notification')
    def test_pipeline_integration_with_telegram(self, mock_send_telegram, mock_fetch_price):
        mock_fetch_price.return_value = self.current_price
        token = uuid.uuid4().hex
        chat_id = str(uuid.uuid4().int)[:8]

        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(self.symbol, self.current_price)

        result = run_threshold_pipeline(
            symbol=self.symbol,
            url=self.url,
            storage_file=self.storage_file,
            threshold=self.threshold,
            telegram_token=token,
            chat_id=chat_id
        )

        self.assertIsInstance(result, dict)
        self.assertIn("price", result)
        self.assertIn("report", result)
        self.assertEqual(result["price"], self.current_price)
        mock_send_telegram.assert_called_once()

    def test_check_market_threshold_logic(self):
        triggered, price = check_market_threshold(
            storage_file=self.storage_file,
            symbol=self.symbol,
            threshold=self.threshold,
            current_price=self.current_price
        )
        self.assertTrue(triggered)
        self.assertEqual(price, self.current_price)

if __name__ == '__main__':
    unittest.main()