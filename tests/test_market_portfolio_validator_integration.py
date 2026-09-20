import unittest
import uuid
import random
import os
from skills.market_portfolio_validator import (
    validate_market_data,
    validate_portfolio_structure,
    validate_market_portfolio_data,
    MarketDataValidationError,
    PortfolioStructureValidationError
)
from skills.market_parser import MarketParser

class TestMarketPortfolioValidatorIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.parser = MarketParser(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_integration_valid_market_data_flow(self):
        random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        random_price = round(random.uniform(10.0, 1500.0), 2)

        self.parser.fetch_and_store(random_symbol, random_price)
        loaded_data = self.parser.load_data(self.storage_file)

        symbol_data = loaded_data.get(random_symbol, {})
        extracted_price = symbol_data.get("price", random_price) if isinstance(symbol_data, dict) else symbol_data

        market_payload = {
            random_symbol: {
                "symbol": random_symbol,
                "price": extracted_price
            }
        }

        validated_single = validate_market_data(market_payload[random_symbol])
        self.assertEqual(validated_single["symbol"], random_symbol)
        self.assertEqual(validated_single["price"], random_price)

        is_valid_pipeline = validate_market_portfolio_data(market_payload)
        self.assertTrue(is_valid_pipeline)

    def test_integration_invalid_portfolio_and_market_types(self):
        random_id = str(uuid.uuid4())
        bad_price = -abs(round(random.uniform(1.0, 100.0), 2))

        invalid_portfolio = {
            "portfolio_id": random_id,
            "assets": [
                {"symbol": "BTC", "price": bad_price}
            ]
        }

        validated_struct = validate_portfolio_structure(invalid_portfolio)
        self.assertEqual(validated_struct["portfolio_id"], random_id)

        corrupted_market_data = {
            "BTC": {
                "symbol": "BTC",
                "price": bad_price
            }
        }

        with self.assertRaises(MarketDataValidationError):
            validate_market_data(corrupted_market_data["BTC"])

        is_valid_pipeline = validate_market_portfolio_data(corrupted_market_data)
        self.assertFalse(is_valid_pipeline)

if __name__ == "__main__":
    unittest.main()
