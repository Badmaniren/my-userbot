import io
import random
import unittest
import uuid

from skills.market_portfolio_dividend_tracker import DividendTracker
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator
from skills.market_portfolio_yield_evaluator import (
    MarketPortfolioYieldEvaluator,
    calculate_net_yield,
    evaluate_portfolio_yield,
)


class TestMarketPortfolioYieldEvaluatorIntegration(unittest.TestCase):
    def setUp(self):
        self.tax_calculator = MarketPortfolioTaxCalculator()
        self.dividend_tracker = DividendTracker(
            db_storage=None,
            tax_calculator=self.tax_calculator,
            api_gateway=None,
        )
        self.evaluator = MarketPortfolioYieldEvaluator(
            dividend_tracker=self.dividend_tracker,
            tax_calculator=self.tax_calculator,
        )

    def test_calculate_net_dividend_yield_returns_random_portfolio_id(self):
        random_portfolio_id = f"port_{uuid.uuid4().hex[:12]}"
        random_value = round(random.uniform(10000.0, 250000.0), 2)

        result = self.evaluator.calculate_net_dividend_yield(
            portfolio_id=random_portfolio_id,
            total_portfolio_value=random_value,
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), random_portfolio_id)
        self.assertIn("net_yield", result)
        self.assertIn("gross_dividends", result)
        self.assertIn("tax_amount", result)
        self.assertIn("net_dividends", result)

        gross = result["gross_dividends"]
        tax = result["tax_amount"]
        net = result["net_dividends"]
        self.assertAlmostEqual(net, gross - tax, places=4)
        if random_value > 0:
            self.assertAlmostEqual(result["net_yield"], net / random_value, places=4)

    def test_evaluate_portfolio_yield_with_holdings_and_extended_metrics(self):
        random_portfolio_id = f"port_ext_{uuid.uuid4().hex[:10]}"
        random_portfolio_val = round(random.uniform(50000.0, 500000.0), 2)
        holdings = [
            {"ticker": f"SYM_{uuid.uuid4().hex[:4].upper()}", "shares": random.randint(10, 100), "price": round(random.uniform(20.0, 200.0), 2)}
        ]

        result = self.evaluator.evaluate_portfolio_yield(
            portfolio_id=random_portfolio_id,
            portfolio_value=random_portfolio_val,
            holdings=holdings,
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), random_portfolio_id)
        self.assertEqual(result.get("portfolio_value"), random_portfolio_val)
        self.assertIn("net_dividend_yield", result)
        self.assertIn("effective_rate", result)
        self.assertIn("currency", result)
        self.assertEqual(result["currency"], "USD")

    def test_evaluate_projected_yield_integration(self):
        ticker = f"TCK_{uuid.uuid4().hex[:5].upper()}"
        shares_count = random.randint(50, 1000)
        portfolio_value = round(random.uniform(20000.0, 100000.0), 2)
        tax_rate = round(random.uniform(0.10, 0.30), 2)

        projected = self.evaluator.evaluate_projected_yield(
            ticker=ticker,
            shares_count=shares_count,
            total_portfolio_value=portfolio_value,
            tax_rate=tax_rate,
        )

        self.assertIsInstance(projected, (int, float))
        self.assertGreaterEqual(projected, 0.0)

    def test_process_yield_stream_integration(self):
        stream_payload = f"dividend_stream_data_{uuid.uuid4().hex}"
        stream = io.StringIO(stream_payload)

        processed = self.evaluator.process_yield_stream(stream)
        self.assertIsNotNone(processed)

    def test_standalone_functions_integration(self):
        random_id_1 = f"standalone_net_{uuid.uuid4().hex[:8]}"
        random_val_1 = round(random.uniform(15000.0, 80000.0), 2)
        res1 = calculate_net_yield(portfolio_id=random_id_1, total_portfolio_value=random_val_1)

        self.assertIsInstance(res1, dict)
        self.assertEqual(res1.get("portfolio_id"), random_id_1)

        random_id_2 = f"standalone_eval_{uuid.uuid4().hex[:8]}"
        random_val_2 = round(random.uniform(25000.0, 95000.0), 2)
        res2 = evaluate_portfolio_yield(portfolio_id=random_id_2, portfolio_value=random_val_2)

        self.assertIsInstance(res2, dict)
        self.assertEqual(res2.get("portfolio_id"), random_id_2)
        self.assertEqual(res2.get("portfolio_value"), random_val_2)


if __name__ == "__main__":
    unittest.main()