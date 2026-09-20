import unittest
import os
import uuid
import random
from skills.market_portfolio_valuation import PortfolioValuation
from skills.market_portfolio_visualizer_v2 import PortfolioVisualizer, generate_ascii_chart
from skills.market_portfolio_alert_dispatcher import dispatch_portfolio_alerts
from skills.market_portfolio_digest import generate_extended_digest


class TestMarketPortfolioDigestIntegration(unittest.TestCase):

    def setUp(self):
        self.unique_id = str(uuid.uuid4())[:8]
        self.storage_file = f"test_storage_{self.unique_id}.json"
        self.symbol = f"TICK_{self.unique_id.upper()}"
        self.url = f"https://example.com/api/{self.symbol.lower()}"
        self.telegram_token = f"token_{self.unique_id}"
        self.chat_id = str(random.randint(100000, 999999))
        
        test_data = {
            self.symbol: [
                {"price": round(random.uniform(10.0, 100.0), 2), "timestamp": "2023-10-01T00:00:00"},
                {"price": round(random.uniform(100.0, 200.0), 2), "timestamp": "2023-10-02T00:00:00"}
            ]
        }
        
        import json
        with open(self.storage_file, "w") as f:
            json.dump(test_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_digest_composition_and_execution(self):
        valuation_inst = PortfolioValuation(self.storage_file)
        summary = valuation_inst.get_total_summary(self.url)
        self.assertIsNotNone(summary)

        visualizer_inst = PortfolioVisualizer(self.storage_file)
        text_report = visualizer_inst.build_text_report(self.symbol)
        self.assertIsInstance(text_report, str)

        ascii_chart = generate_ascii_chart([x["price"] for x in valuation_inst.load_data(self.storage_file).get(self.symbol, [])])
        self.assertIsInstance(ascii_chart, str)

        digest_result = generate_extended_digest(
            storage_file=self.storage_file,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        self.assertIsNotNone(digest_result)
        if isinstance(digest_result, dict):
            self.assertIn("status", digest_result)
            self.assertEqual(digest_result["status"], "success")


if __name__ == "__main__":
    unittest.main()