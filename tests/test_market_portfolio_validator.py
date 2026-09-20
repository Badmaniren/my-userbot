import unittest
from unittest.mock import patch
import uuid
import random

from skills.market_portfolio_validator import (
    MarketDataValidationError,
    PortfolioStructureValidationError,
    load_stream_data,
    validate_market_data,
    validate_portfolio_structure,
    validate_market_portfolio_data
)


class TestMarketPortfolioValidator(unittest.TestCase):

    def test_load_stream_data_stub(self):
        result = load_stream_data()
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    def test_validate_market_data_success(self):
        rand_symbol = uuid.uuid4().hex[:6].upper()
        rand_price = round(random.uniform(1.0, 10000.0), 2)
        raw_data = {"symbol": rand_symbol, "price": rand_price}

        validated = validate_market_data(raw_data)
        self.assertEqual(validated["symbol"], rand_symbol)
        self.assertEqual(validated["price"], rand_price)

    def test_validate_market_data_not_dict(self):
        invalid_inputs = [
            uuid.uuid4().hex,
            random.randint(1, 1000),
            random.random(),
            [uuid.uuid4().hex, random.randint(1, 100)],
            None
        ]
        for item in invalid_inputs:
            with self.subTest(item=item):
                with self.assertRaises(MarketDataValidationError):
                    validate_market_data(item)

    def test_validate_market_data_missing_fields(self):
        rand_symbol = uuid.uuid4().hex[:6].upper()
        rand_price = round(random.uniform(1.0, 1000.0), 2)

        incomplete_data = [
            {},
            {"symbol": rand_symbol},
            {"price": rand_price},
            {uuid.uuid4().hex: uuid.uuid4().hex}
        ]
        for item in incomplete_data:
            with self.subTest(item=item):
                with self.assertRaises(MarketDataValidationError):
                    validate_market_data(item)

    def test_validate_market_data_invalid_price_type(self):
        rand_symbol = uuid.uuid4().hex[:6].upper()
        invalid_prices = [
            uuid.uuid4().hex,
            str(random.randint(10, 100)),
            [random.randint(1, 10)],
            {uuid.uuid4().hex: random.randint(1, 10)},
            True,
            False,
            None
        ]
        for bad_price in invalid_prices:
            with self.subTest(bad_price=bad_price):
                raw_data = {"symbol": rand_symbol, "price": bad_price}
                with self.assertRaises(MarketDataValidationError):
                    validate_market_data(raw_data)

    def test_validate_market_data_invalid_symbol_type(self):
        rand_price = round(random.uniform(1.0, 100.0), 2)
        invalid_symbols = [
            123,
            12.34,
            "",
            "   ",
            True,
            False,
            ["BTC"],
            {"symbol": "BTC"},
            None
        ]
        for bad_symbol in invalid_symbols:
            with self.subTest(bad_symbol=bad_symbol):
                raw_data = {"symbol": bad_symbol, "price": rand_price}
                with self.assertRaises(MarketDataValidationError):
                    validate_market_data(raw_data)

    def test_validate_market_data_negative_price(self):
        rand_symbol = uuid.uuid4().hex[:6].upper()
        negative_prices = [
            -round(random.uniform(0.01, 1000.0), 2),
            -random.randint(1, 500)
        ]
        for neg_price in negative_prices:
            with self.subTest(neg_price=neg_price):
                raw_data = {"symbol": rand_symbol, "price": neg_price}
                with self.assertRaises(MarketDataValidationError):
                    validate_market_data(raw_data)

    def test_validate_portfolio_structure_success(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_asset_symbol = uuid.uuid4().hex[:5].upper()
        rand_amount = random.randint(1, 100)

        portfolio = {
            "portfolio_id": rand_portfolio_id,
            "assets": [
                {"symbol": rand_asset_symbol, "amount": rand_amount}
            ]
        }

        validated = validate_portfolio_structure(portfolio)
        self.assertEqual(validated["portfolio_id"], rand_portfolio_id)
        self.assertIsInstance(validated["assets"], list)
        self.assertEqual(len(validated["assets"]), 1)
        self.assertEqual(validated["assets"][0]["symbol"], rand_asset_symbol)

    def test_validate_portfolio_structure_not_dict(self):
        invalid_portfolios = [
            uuid.uuid4().hex,
            random.randint(1, 1000),
            [uuid.uuid4().hex],
            None
        ]
        for item in invalid_portfolios:
            with self.subTest(item=item):
                with self.assertRaises(PortfolioStructureValidationError):
                    validate_portfolio_structure(item)

    def test_validate_portfolio_structure_missing_keys(self):
        rand_id = uuid.uuid4().hex
        incomplete_portfolios = [
            {},
            {"portfolio_id": rand_id},
            {"assets": []},
            {uuid.uuid4().hex: uuid.uuid4().hex}
        ]
        for item in incomplete_portfolios:
            with self.subTest(item=item):
                with self.assertRaises(PortfolioStructureValidationError):
                    validate_portfolio_structure(item)

    def test_validate_portfolio_structure_invalid_assets_type(self):
        rand_id = uuid.uuid4().hex
        invalid_assets = [
            uuid.uuid4().hex,
            random.randint(1, 100),
            not_a_list := {"symbol": uuid.uuid4().hex},
            None
        ]
        for bad_assets in invalid_assets:
            with self.subTest(bad_assets=bad_assets):
                portfolio = {
                    "portfolio_id": rand_id,
                    "assets": bad_assets
                }
                with self.assertRaises(PortfolioStructureValidationError):
                    validate_portfolio_structure(portfolio)

    def test_validate_portfolio_structure_invalid_asset_item(self):
        rand_id = uuid.uuid4().hex
        invalid_asset_items = [
            [uuid.uuid4().hex],
            [random.randint(1, 100)],
            [None],
            [{"symbol": uuid.uuid4().hex}, uuid.uuid4().hex]
        ]
        for bad_items in invalid_asset_items:
            with self.subTest(bad_items=bad_items):
                portfolio = {
                    "portfolio_id": rand_id,
                    "assets": bad_items
                }
                with self.assertRaises(PortfolioStructureValidationError):
                    validate_portfolio_structure(portfolio)

    def test_validate_market_portfolio_data_integration_success(self):
        rand_symbol_1 = uuid.uuid4().hex[:4].upper()
        rand_symbol_2 = uuid.uuid4().hex[:4].upper()
        price_1 = round(random.uniform(10.0, 500.0), 2)
        price_2 = round(random.uniform(500.1, 2000.0), 2)

        raw_data = {
            rand_symbol_1: {"symbol": rand_symbol_1, "price": price_1},
            rand_symbol_2: {"symbol": rand_symbol_2, "price": price_2}
        }

        result = validate_market_portfolio_data(raw_data)
        self.assertTrue(result)

    def test_validate_market_portfolio_data_integration_failure(self):
        rand_symbol = uuid.uuid4().hex[:4].upper()
        bad_structures = [
            {},
            [],
            uuid.uuid4().hex,
            {rand_symbol: uuid.uuid4().hex},
            {rand_symbol: {"symbol": rand_symbol, "price": -10.0}},
            None
        ]
        for bad_data in bad_structures:
            with self.subTest(bad_data=bad_data):
                result = validate_market_portfolio_data(bad_data)
                self.assertFalse(result)

    def test_validate_market_portfolio_data_exception_handling(self):
        rand_symbol = uuid.uuid4().hex[:5].upper()
        with patch("skills.market_portfolio_validator.validate_market_data", side_effect=MarketDataValidationError):
            raw_data = {rand_symbol: {"symbol": rand_symbol, "price": 100.0}}
            result = validate_market_portfolio_data(raw_data)
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
