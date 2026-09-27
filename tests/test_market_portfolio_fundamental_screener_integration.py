import unittest
import uuid
import random
import os
from skills.market_portfolio_fundamental_screener import market_portfolio_fundamental_screener
from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent

class TestMarketPortfolioFundamentalScreenerIntegration(unittest.TestCase):

    def test_fundamental_screener_integration(self):
        portfolio_id = f"test_port_{uuid.uuid4().hex[:8]}"
        asset_ticker = f"TICK_{random.randint(1000, 9999)}"

        raw_price = round(random.uniform(10.0, 500.0), 2)
        raw_eps = round(random.uniform(1.0, 25.0), 2)
        raw_bvps = round(random.uniform(5.0, 100.0), 2)
        raw_sps = round(random.uniform(2.0, 50.0), 2)
        raw_de = round(random.uniform(0.1, 2.5), 2)

        payload = {
            "portfolio_id": portfolio_id,
            "assets": [
                {
                    "ticker": asset_ticker,
                    "price": raw_price,
                    "eps": raw_eps,
                    "book_value_per_share": raw_bvps,
                    "sales_per_share": raw_sps,
                    "debt_to_equity": raw_de
                }
            ],
            "criteria": {
                "max_pe": 30.0,
                "max_pb": 5.0,
                "max_debt_to_equity": 2.0
            }
        }

        collector_result = market_portfolio_collector_agent(payload)
        self.assertIsNotNone(collector_result)

        screening_result = market_portfolio_fundamental_screener(payload)

        self.assertIn("filtered_assets", screening_result)
        self.assertIn("multipliers", screening_result)

        persisted_data = db_storage("get", portfolio_id)
        self.assertIsNotNone(persisted_data)

        output_filepath = f"data_reports/fundamental_screen_{portfolio_id}.json"
        has_file_created = os.path.exists(output_filepath) or "report_path" in screening_result
        self.assertTrue(has_file_created, "Интеграционный тест требует фиксации результатов в хранилище или файл.")

if __name__ == "__main__":
    unittest.main()