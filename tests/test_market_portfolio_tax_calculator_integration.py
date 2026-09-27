import unittest
import uuid
import random
import os
from skills.market_portfolio_tax_calculator import calculate_portfolio_taxes
from skills.db_storage import save_tax_report, get_tax_report
from skills.market_parser import parse_market_deals

class TestMarketPortfolioTaxCalculatorIntegration(unittest.TestCase):

    def test_end_to_end_tax_calculation_and_persistence(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        user_id = random.randint(10000, 99999)
        
        raw_deal_data = f"BUY,AAPL,{random.randint(10, 100)},{random.uniform(100.0, 200.0)},2020-01-15\n" \
                        f"SELL,AAPL,{random.randint(1, 10)},{random.uniform(210.0, 300.0)},2023-05-20"
        
        parsed_deals = parse_market_deals(raw_deal_data)
        
        holding_period_years = random.choice([1, 2, 3, 5])
        dividend_income = round(random.uniform(50.0, 5000.0), 2)
        
        tax_result = calculate_portfolio_taxes(
            portfolio_id=portfolio_id,
            user_id=user_id,
            deals=parsed_deals,
            holding_period=holding_period_years,
            dividends=dividend_income
        )
        
        self.assertIn("total_tax_due", tax_result)
        self.assertEqual(tax_result["portfolio_id"], portfolio_id)
        self.assertGreaterEqual(tax_result["total_tax_due"], 0.0)
        
        report_id = f"rep_{uuid.uuid4().hex}"
        save_tax_report(report_id, tax_result)
        
        retrieved_data = get_tax_report(report_id)
        
        self.assertIsNotNone(retrieved_data)
        self.assertEqual(retrieved_data["portfolio_id"], portfolio_id)
        self.assertEqual(retrieved_data["total_tax_due"], tax_result["total_tax_due"])

if __name__ == "__main__":
    unittest.main()