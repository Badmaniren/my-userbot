import unittest
import uuid
import random
import os
from skills.market_portfolio_tax_report_exporter import market_portfolio_tax_report_exporter
from skills.market_portfolio_tax_calculator import market_portfolio_tax_calculator
from skills.market_portfolio_dividend_tracker import market_portfolio_dividend_tracker
from skills.db_storage import db_storage

class IntegrationTestMarketPortfolioTaxReportExporter(unittest.TestCase):
    def test_tax_report_export_integration(self):
        portfolio_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        tax_year = random.randint(2020, 2026)
        dividend_amount = round(random.uniform(100.0, 50000.0), 2)

        dividend_data = {
            "portfolio_id": portfolio_id,
            "user_id": user_id,
            "year": tax_year,
            "amount": dividend_amount,
            "currency": "USD"
        }

        div_result = market_portfolio_dividend_tracker(dividend_data)
        self.assertIsNotNone(div_result)

        calc_payload = {
            "portfolio_id": portfolio_id,
            "tax_year": tax_year
        }
        tax_calculation = market_portfolio_tax_calculator(calc_payload)
        self.assertIsNotNone(tax_calculation)

        export_format = random.choice(["csv", "pdf", "json"])
        export_payload = {
            "portfolio_id": portfolio_id,
            "tax_year": tax_year,
            "format": export_format,
            "include_dividends": True
        }

        export_result = market_portfolio_tax_report_exporter(export_payload)

        self.assertIsInstance(export_result, dict)
        self.assertIn("report_id", export_result)
        self.assertIn("file_path", export_result)

        generated_file = export_result["file_path"]
        self.assertTrue(os.path.exists(generated_file), f"Generated report file {generated_file} does not exist on disk.")

        db_check = db_storage({
            "action": "get_tax_report",
            "report_id": export_result["report_id"]
        })
        self.assertIsNotNone(db_check)

        if os.path.exists(generated_file):
            os.remove(generated_file)

if __name__ == "__main__":
    unittest.main()