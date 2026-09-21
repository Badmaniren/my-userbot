import unittest
import os
import tempfile
import uuid
import random
import json
from unittest.mock import patch

from skills.market_portfolio_digest import (
    generate_portfolio_digest,
    generate_extended_digest,
    PortfolioDigestManager,
)


class TestMarketPortfolioDigestIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(
            self.temp_dir.name, f"digest_storage_{uuid.uuid4().hex}.json"
        )
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"https://api.example.com/{uuid.uuid4().hex}"
        self.token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))

        sample_data = {
            self.symbol: {"buy_price": 90.0, "quantity": 2.0}
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(sample_data, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("skills.market_portfolio_digest.send_telegram_notification")
    @patch("skills.market_portfolio_valuation.MarketParser.fetch_price")
    def test_generate_portfolio_digest_integration(
        self, mock_fetch_price, mock_send
    ):
        mock_fetch_price.return_value = 105.0

        result = generate_portfolio_digest(
            self.symbol, self.url, self.token, self.chat_id, self.storage_file
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], self.symbol)
        self.assertIn("valuation", result)
        self.assertIn("report", result)
        self.assertIn("performance_metrics", result)

    @patch("skills.market_portfolio_digest.send_telegram_notification")
    @patch("skills.market_portfolio_valuation.MarketParser.fetch_price")
    def test_generate_extended_digest_integration(
        self, mock_fetch_price, mock_send
    ):
        mock_fetch_price.return_value = 105.0

        status = generate_extended_digest(
            self.storage_file, self.symbol, self.url, self.token, self.chat_id
        )

        self.assertIsInstance(status, dict)
        self.assertEqual(status["status"], "success")
        self.assertEqual(status["symbol"], self.symbol)
        self.assertIn("summary", status)
        self.assertIn("report", status)

    @patch("skills.market_portfolio_valuation.MarketParser.fetch_price")
    def test_portfolio_digest_manager_integration(self, mock_fetch_price):
        mock_fetch_price.return_value = 105.0

        manager = PortfolioDigestManager(self.storage_file)
        digest = manager.compile_digest(self.symbol, self.url)

        self.assertIsInstance(digest, dict)
        self.assertEqual(digest["symbol"], self.symbol)
        self.assertIn("summary", digest)
        self.assertIn("ascii_chart", digest)

    @patch("skills.market_portfolio_visualizer_v2.send_telegram_notification")
    def test_portfolio_digest_manager_render_and_send_integration(
        self, mock_send
    ):
        manager = PortfolioDigestManager(self.storage_file)
        manager.render_and_send(self.symbol, self.token, self.chat_id)
        mock_send.assert_called_once()


if __name__ == "__main__":
    unittest.main()
