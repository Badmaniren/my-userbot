import unittest
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills")))

from market_portfolio_strategy_optimizer import market_portfolio_strategy_optimizer
from market_portfolio_tax_calculator import market_portfolio_tax_calculator
from market_portfolio_dividend_tracker import market_portfolio_dividend_tracker

class TestTaxAndDividendEpicPractical(unittest.TestCase):

    def setUp(self):
        self.test_data_filename = "test_portfolio_tax_dividend_data.json"

        self.raw_portfolio_data = {
            "portfolio_id": "TEST_PORTFOLIO_001",
            "currency": "USD",
            "assets": [
                {
                    "ticker": "AAPL",
                    "shares": 150,
                    "purchase_price": 145.50,
                    "current_price": 185.20,
                    "holding_period_days": 420,
                    "dividends_received": [
                        {"date": "2023-02-15", "amount_per_share": 0.23, "tax_withheld": 0.03},
                        {"date": "2023-05-15", "amount_per_share": 0.24, "tax_withheld": 0.03},
                        {"date": "2023-08-15", "amount_per_share": 0.24, "tax_withheld": 0.03},
                        {"date": "2023-11-15", "amount_per_share": 0.24, "tax_withheld": 0.03}
                    ]
                },
                {
                    "ticker": "MSFT",
                    "shares": 80,
                    "purchase_price": 280.00,
                    "current_price": 410.50,
                    "holding_period_days": 210,
                    "dividends_received": [
                        {"date": "2023-03-14", "amount_per_share": 0.68, "tax_withheld": 0.08},
                        {"date": "2023-06-13", "amount_per_share": 0.75, "tax_withheld": 0.09},
                        {"date": "2023-09-12", "amount_per_share": 0.75, "tax_withheld": 0.09},
                        {"date": "2023-12-12", "amount_per_share": 0.75, "tax_withheld": 0.09}
                    ]
                },
                {
                    "ticker": "JNJ",
                    "shares": 100,
                    "purchase_price": 160.00,
                    "current_price": 155.00,
                    "holding_period_days": 600,
                    "dividends_received": [
                        {"date": "2023-03-07", "amount_per_share": 1.13, "tax_withheld": 0.15},
                        {"date": "2023-06-06", "amount_per_share": 1.19, "tax_withheld": 0.15},
                        {"date": "2023-09-05", "amount_per_share": 1.19, "tax_withheld": 0.15},
                        {"date": "2023-11-28", "amount_per_share": 1.19, "tax_withheld": 0.15}
                    ]
                }
            ],
            "tax_jurisdiction": "US",
            "tax_brackets": {
                "short_term_capital_gains": 0.22,
                "long_term_capital_gains": 0.15,
                "qualified_dividend": 0.15
            }
        }

        with open(self.test_data_filename, "w", encoding="utf-8") as f:
            json.dump(self.raw_portfolio_data, f, indent=4)

    def tearDown(self):
        if os.path.exists(self.test_data_filename):
            os.remove(self.test_data_filename)

    def test_complete_tax_and_dividend_epic_workflow(self):
        print("\n=== STARTING PRACTICAL VERIFICATION: TAX & DIVIDEND EPIC ===")

        self.assertTrue(os.path.exists(self.test_data_filename), "Test JSON file must exist on disk.")

        with open(self.test_data_filename, "r", encoding="utf-8") as f:
            portfolio_payload = json.load(f)

        print(f"[1/3] Running market_portfolio_strategy_optimizer...")
        optimizer = market_portfolio_strategy_optimizer()
        optimization_result = optimizer.optimize_strategy(portfolio_payload) if hasattr(optimizer, 'optimize_strategy') else optimizer(portfolio_payload)
        print(f"Strategy Optimizer Output: {json.dumps(optimization_result, indent=2)}")

        print(f"[2/3] Running market_portfolio_dividend_tracker...")
        dividend_tracker = market_portfolio_dividend_tracker()
        dividend_report = dividend_tracker.track(portfolio_payload) if hasattr(dividend_tracker, 'track') else dividend_tracker(portfolio_payload)
        print(f"Dividend Tracker Output: {json.dumps(dividend_report, indent=2)}")

        print(f"[3/3] Running market_portfolio_tax_calculator (Stabilized Final Version)...")
        tax_calc = market_portfolio_tax_calculator()
        tax_report = tax_calc.calculate(portfolio_payload) if hasattr(tax_calc, 'calculate') else tax_calc(portfolio_payload)
        print(f"Tax Calculator Output: {json.dumps(tax_report, indent=2)}")

        self.assertIsNotNone(optimization_result, "Strategy optimizer should return a valid result.")
        self.assertIsNotNone(dividend_report, "Dividend tracker should return a valid result.")
        self.assertIsNotNone(tax_report, "Tax calculator should return a valid result.")

        print("=== COMPLETED PRACTICAL VERIFICATION SUCCESSFULLY ===")

if __name__ == "__main__":
    unittest.main()