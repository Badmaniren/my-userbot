import unittest
import uuid
import random
from skills.market_portfolio_multi_exchange_arb_detector import market_portfolio_multi_exchange_arb_detector, start_new

class TestMarketPortfolioMultiExchangeArbDetectorIntegration(unittest.TestCase):
    def test_multi_exchange_arbitrage_pipeline(self):
        run_id = str(uuid.uuid4())
        symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD"]
        selected_symbol = random.choice(symbols)

        exchanges_pool = ["binance", "kraken", "coinbase", "bybit", "okx"]
        selected_exchanges = random.sample(exchanges_pool, 2)

        min_spread = round(random.uniform(10.0, 50.0), 2)

        arb_input = {
            "run_id": run_id,
            "symbol": selected_symbol,
            "min_spread_threshold": min_spread,
            "exchanges_to_scan": selected_exchanges
        }

        result = market_portfolio_multi_exchange_arb_detector(arb_input)

        self.assertIn("opportunities", result)
        self.assertIn("execution_path", result)
        self.assertEqual(result["execution_path"], "direct_arbitrage_pipeline")

        opportunities = result["opportunities"]
        self.assertGreaterEqual(len(opportunities), 1)

        opp = opportunities[0]
        self.assertEqual(opp["symbol"], selected_symbol)
        self.assertEqual(opp["buy_exchange"], selected_exchanges[0])
        self.assertEqual(opp["sell_exchange"], selected_exchanges[1])
        self.assertIsInstance(opp["spread"], float)
        self.assertGreater(opp["spread"], 0.0)

        mock_deps = {
            "market_parser": None,
            "market_anomaly_detector": None,
            "extractor_tool_1790087207": None
        }
        start_result = start_new(mock_deps)
        self.assertEqual(start_result.get("status"), "ok")
        self.assertIn("arbitrage_index", start_result)

if __name__ == "__main__":
    unittest.main()