import unittest
import uuid
import random
from skills.db_storage import db_storage
from skills.market_portfolio_rebalancer import market_portfolio_rebalancer, MarketPortfolioRebalancer

class TestMarketPortfolioRebalancerIntegration(unittest.TestCase):
    def test_rebalance_integration_flow(self):
        portfolio_id = str(uuid.uuid4())
        symbol_btc = "BTC_" + uuid.uuid4().hex[:6].upper()
        symbol_eth = "ETH_" + uuid.uuid4().hex[:6].upper()

        price_btc = round(random.uniform(30000.0, 50000.0), 2)
        price_eth = round(random.uniform(2000.0, 4000.0), 2)

        initial_state = {
            "assets": {
                symbol_btc: {
                    "quantity": 2.0,
                    "target_weight": 0.8
                },
                symbol_eth: {
                    "quantity": 5.0,
                    "target_weight": 0.2
                }
            },
            "trigger_threshold": 0.05,
            "min_order_value": 50.0
        }

        db_storage("save_portfolio", (portfolio_id, initial_state))

        config = {
            "portfolio_id": portfolio_id,
            "market_data": {
                "symbol": symbol_btc,
                "price": price_btc
            }
        }

        result = market_portfolio_rebalancer(config)

        self.assertIn("orders", result)
        self.assertIn("deviations", result)
        self.assertIsInstance(result["orders"], list)
        self.assertIsInstance(result["deviations"], dict)

        saved_orders = db_storage("get_orders", portfolio_id)
        self.assertIsNotNone(saved_orders)

    def class_methods_direct_integration(self):
        rebalancer = MarketPortfolioRebalancer()
        stream_payload = {"event": uuid.uuid4().hex, "price": random.uniform(100, 500)}
        parsed = rebalancer.process_market_stream(stream_payload)
        self.assertIsNotNone(parsed)

if __name__ == "__main__":
    unittest.main()