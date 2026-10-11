import unittest
import uuid
import random
import os

from skills.market_portfolio_valuation import PortfolioValuation
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator
from skills.market_portfolio_net_yield_evaluator import evaluate_net_yield

class TestMarketPortfolioNetYieldEvaluatorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_storage = f"test_portfolio_{uuid.uuid4()}.json"
        self.portfolio_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())
        self.random_url = f"file://{self.test_storage}"
        
        with open(self.test_storage, "w") as f:
            f.write("{}")

    def tearDown(self):
        if os.path.exists(self.test_storage):
            os.remove(self.test_storage)

    def test_net_yield_evaluator_composition(self):
        valuation_engine = PortfolioValuation(self.test_storage)
        tax_calculator = MarketPortfolioTaxCalculator()

        self.assertIsNotNone(valuation_engine)
        self.assertIsNotNone(tax_calculator)

        deals_count = random.randint(1, 5)
        deals = []
        for _ in range(deals_count):
            deals.append({
                "deal_id": str(uuid.uuid4()),
                "amount": round(random.uniform(100.0, 10000.0), 2),
                "type": random.choice(["BUY", "SELL"])
            })

        holding_period = random.randint(30, 1000)
        dividends = round(random.uniform(0.0, 500.0), 2)

        tax_result = calculate_portfolio_taxes(
            portfolio_id=self.portfolio_id,
            user_id=self.user_id,
            deals=deals,
            holding_period=holding_period,
            dividends=dividends
        )

        self.assertIsInstance(tax_result, (dict, float, int))

        valuation_summary = valuation_engine.get_total_summary(self.random_url)
        self.assertIsInstance(valuation_summary, (dict, float, int))

        net_yield_output = evaluate_net_yield(
            portfolio_id=self.portfolio_id,
            url=self.random_url
        )

        self.assertIsInstance(net_yield_output, dict)
        self.assertIn("portfolio_id", net_yield_output)
        self.assertEqual(net_yield_output["portfolio_id"], self.portfolio_id)
        self.assertIn("net_yield", net_yield_output)

if __name__ == "__main__":
    unittest.main()