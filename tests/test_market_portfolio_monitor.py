import unittest
from unittest.mock import patch
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, run_pipeline

class TestMarketPortfolioMonitorStartNew(unittest.TestCase):
    def setUp(self):
        self.symbol = f"COIN_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.randomcrypto.org/{uuid.uuid4().hex[:4]}"
        self.telegram_token = f"{random.randint(100000, 999999)}:AAG{uuid.uuid4().hex[:15]}"
        self.chat_id = f"-{random.randint(100000000, 999999999)}"
        self.storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_start_new_success_execution(self):
        result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.storage_file))

        with open(self.storage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], 0.0)

    @patch("skills.market_portfolio_monitor.run_market_telegram_pipeline")
    def test_start_new_calls_pipeline_with_correct_args(self, mock_telegram_pipeline):
        mock_telegram_pipeline.return_value = {
            "status": "success",
            "symbol": self.symbol,
            "price": 0.0,
            "chat_id": self.chat_id,
            "url": self.url
        }

        result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(result)
        mock_telegram_pipeline.assert_called_once_with(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )