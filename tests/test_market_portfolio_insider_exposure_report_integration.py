import unittest
import uuid
import random
import os
from skills.market_portfolio_insider_exposure_report import generate_insider_exposure_report
from skills.db_storage import save_record, get_record
from skills.market_parser import parse_market_data

class TestMarketPortfolioInsiderExposureReportIntegration(unittest.TestCase):
    def test_insider_exposure_report_end_to_end(self):
        unique_symbol = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        random_price = round(random.uniform(10.0, 1000.0), 2)
        random_volume = random.randint(1000, 500000)

        raw_market_payload = {
            "symbol": unique_symbol,
            "price": random_price,
            "volume": random_volume,
            "insider_transactions": [
                {"shares": random.randint(100, 5000), "type": "BUY"}
            ]
        }

        parsed_data = parse_market_data(raw_market_payload)
        self.assertIsNotNone(parsed_data)

        db_key = f"exposure_{uuid.uuid4().hex}"
        save_record(db_key, parsed_data)

        stored_record = get_record(db_key)
        self.assertEqual(stored_record["symbol"], unique_symbol)

        report_result = generate_insider_exposure_report(db_key)

        self.assertIsInstance(report_result, dict)
        self.assertIn("report_id", report_result)
        self.assertEqual(report_result["target_symbol"], unique_symbol)
        self.assertEqual(report_result["analyzed_price"], random_price)

        expected_filename = f"report_{report_result['report_id']}.txt"
        self.assertTrue(os.path.exists(expected_filename) or report_result.get("persisted") is True)

        if os.path.exists(expected_filename):
            os.remove(expected_filename)

if __name__ == "__main__":
    unittest.main()