import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_macro_correlation_scanner import market_portfolio_macro_correlation_scanner
from skills.db_storage import db_storage
from skills.market_parser import market_parser
from skills.market_portfolio_integration_hub import market_portfolio_integration_hub

class TestMarketPortfolioMacroCorrelationScannerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_db_path = tempfile.mktemp(suffix=".db")
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.asset_ticker = f"TICK_{random.randint(1000, 9999)}"
        self.macro_factor = f"MACRO_{random.choice(['CPI', 'GDP', 'FED_RATE', 'OIL'])}_{random.randint(10, 99)}"
        
        db_storage.initialize_database(self.test_db_path)
        
    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_macro_correlation_scanner_end_to_end(self):
        raw_market_data = {
            "ticker": self.asset_ticker,
            "price": round(random.uniform(10.0, 500.0), 2),
            "volume": random.randint(1000, 1000000),
            "macro_indicator": self.macro_factor,
            "indicator_value": round(random.uniform(-5.0, 15.0), 2)
        }
        
        parsed_data = market_parser.parse_raw_market_payload(raw_market_data)
        self.assertIsNotNone(parsed_data)

        db_storage.save_market_entity(self.test_db_path, self.portfolio_id, parsed_data)

        integration_context = market_portfolio_integration_hub.prepare_context(
            portfolio_id=self.portfolio_id,
            db_uri=self.test_db_path
        )
        self.assertIn("portfolio_id", integration_context)

        scan_result = market_portfolio_macro_correlation_scanner.scan_macro_correlations(
            portfolio_id=self.portfolio_id,
            integration_hub=integration_context,
            threshold=round(random.uniform(0.5, 0.9), 2)
        )

        self.assertIsInstance(scan_result, dict)
        self.assertIn("correlation_matrix", scan_result)
        self.assertIn("systemic_risks_detected", scan_result)
        
        risk_entries = scan_result.get("systemic_risks_detected", [])
        self.assertIsInstance(risk_entries, list)

        verification_record = db_storage.get_audit_trail(self.test_db_path, self.portfolio_id)
        self.assertIsNotNone(verification_er := verification_record)

if __name__ == "__main__":
    unittest.main()