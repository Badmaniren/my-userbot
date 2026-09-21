import unittest
import os
import uuid
import random
from skills.market_portfolio_digest import (
    generate_portfolio_digest,
    generate_extended_digest,
    PortfolioDigestManager
)


class TestMarketPortfolioDigestIntegration(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_portfolio_{self.random_suffix}.json"
        self.symbol = f"TICK_{random.randint(100, 999)}"
        self.url = f"http://example.com/api/market/{self.random_suffix}"
        self.telegram_token = f"token_{self.random_suffix}"
        self.chat_id = str(random.randint(100000, 999999))

        with open(self.storage_file, "w") as f:
            f.write("{}")

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_generate_portfolio_digest_integration(self):
        result = generate_portfolio_digest(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertIsInstance(result, dict)
        self.assertIn("symbol", result)
        self.assertEqual(result["symbol"], self.symbol)
        self.assertIn("valuation", result)
        self.assertIn("report", result)

    def test_generate_extended_digest_integration(self):
        result = generate_extended_digest(
            storage_file=self.storage_file,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("symbol"), self.symbol)

    def test_portfolio_digest_manager_integration(self):
        manager = PortfolioDigestManager(self.storage_file)

        compile_result = manager.compile_digest(self.symbol, self.url)
        self.assertIsInstance(compile_result, dict)
        self.assertEqual(compile_result.get("symbol"), self.symbol)
        self.assertIn("summary", compile_result)
        self.assertIn("ascii_chart", compile_result)

        render_result = manager.render_and_send(self.symbol, self.telegram_token, self.chat_id)
        self.assertTrue(render_result)


if __name__ == "__main__":
    unittest.main()