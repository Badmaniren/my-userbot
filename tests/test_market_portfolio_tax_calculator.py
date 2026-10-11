import io
import random
import string
import types
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.market_portfolio_tax_calculator import (
    MarketPortfolioTaxCalculator,
    calculate_portfolio_taxes,
)


def _gen_random_str(length=12):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


class TestMarketPortfolioTaxCalculator(unittest.TestCase):
    def test_init_sets_dynamic_kwargs(self):
        random_key_1 = "field_" + uuid.uuid4().hex[:8]
        random_val_1 = uuid.uuid4().hex
        random_key_2 = "metric_" + uuid.uuid4().hex[:8]
        random_val_2 = random.randint(100, 10000)

        kwargs = {random_key_1: random_val_1, random_key_2: random_val_2}
        calculator = MarketPortfolioTaxCalculator(**kwargs)

        self.assertTrue(hasattr(calculator, random_key_1))
        self.assertEqual(getattr(calculator, random_key_1), random_val_1)
        self.assertTrue(hasattr(calculator, random_key_2))
        self.assertEqual(getattr(calculator, random_key_2), random_val_2)

    def test_calculate_tax_without_db_storage(self):
        calculator = MarketPortfolioTaxCalculator()
        random_portfolio_id = "port_" + uuid.uuid4().hex
        tax = calculator.calculate_tax(random_portfolio_id)
        self.assertEqual(tax, 0.0)

    def test_calculate_tax_with_none_db_storage(self):
        calculator = MarketPortfolioTaxCalculator(db_storage=None)
        random_portfolio_id = "port_" + uuid.uuid4().hex
        tax = calculator.calculate_tax(random_portfolio_id)
        self.assertEqual(tax, 0.0)

    def test_calculate_tax_portfolio_not_found(self):
        mock_storage = MagicMock()
        random_portfolio_id = "port_" + uuid.uuid4().hex
        mock_storage.get_portfolio.return_value = None

        calculator = MarketPortfolioTaxCalculator(db_storage=mock_storage)
        tax = calculator.calculate_tax(random_portfolio_id)

        mock_storage.get_portfolio.assert_called_once_with(random_portfolio_id)
        self.assertEqual(tax, 0.0)

    def test_calculate_tax_valid_portfolio(self):
        mock_storage = MagicMock()
        random_portfolio_id = "port_" + uuid.uuid4().hex
        sell_price = round(random.uniform(150.0, 500.0), 2)
        purchase_price = round(random.uniform(50.0, 140.0), 2)
        shares = random.randint(1, 500)

        portfolio_data = {
            "sell_price": sell_price,
            "purchase_price": purchase_price,
            "shares": shares,
        }
        mock_storage.get_portfolio.return_value = portfolio_data

        expected_profit = (sell_price - purchase_price) * shares
        expected_tax = round(expected_profit * 0.13, 2)

        calculator = MarketPortfolioTaxCalculator(db_storage=mock_storage)
        result_tax = calculator.calculate_tax(random_portfolio_id)

        mock_storage.get_portfolio.assert_called_once_with(random_portfolio_id)
        self.assertEqual(result_tax, expected_tax)

    def test_process_dividend_stream_without_parser(self):
        calculator = MarketPortfolioTaxCalculator()
        random_stream = io.BytesIO(uuid.uuid4().bytes)
        result = calculator.process_dividend_stream(random_stream)
        self.assertIsNone(result)

    def test_process_dividend_stream_parser_missing_method(self):
        invalid_parser = object()
        calculator = MarketPortfolioTaxCalculator(market_parser=invalid_parser)
        random_stream = io.BytesIO(uuid.uuid4().bytes)
        result = calculator.process_dividend_stream(random_stream)
        self.assertIsNone(result)

    def test_process_dividend_stream_success(self):
        mock_parser = MagicMock()
        random_stream_id = "stream_" + uuid.uuid4().hex
        mock_parser.parse_stream.return_value = {
            "stream_id": random_stream_id,
            "random_payload": uuid.uuid4().hex,
        }

        random_bytes = uuid.uuid4().bytes * 4
        stream_payload = io.BytesIO(random_bytes)

        calculator = MarketPortfolioTaxCalculator(market_parser=mock_parser)
        stream_id = calculator.process_dividend_stream(stream_payload)

        mock_parser.parse_stream.assert_called_once_with(stream_payload)
        self.assertEqual(stream_id, random_stream_id)

    def test_process_dividend_stream_invalid_parser_return_type(self):
        mock_parser = MagicMock()
        mock_parser.parse_stream.return_value = "invalid_non_dict_response"

        random_stream = io.BytesIO(uuid.uuid4().bytes)
        calculator = MarketPortfolioTaxCalculator(market_parser=mock_parser)
        result = calculator.process_dividend_stream(random_stream)

        mock_parser.parse_stream.assert_called_once_with(random_stream)
        self.assertIsNone(result)

    def test_process_dividend_stream_dict_missing_stream_id(self):
        mock_parser = MagicMock()
        mock_parser.parse_stream.return_value = {
            "not_stream_id": uuid.uuid4().hex
        }

        random_stream = io.BytesIO(uuid.uuid4().bytes)
        calculator = MarketPortfolioTaxCalculator(market_parser=mock_parser)
        result = calculator.process_dividend_stream(random_stream)

        mock_parser.parse_stream.assert_called_once_with(random_stream)
        self.assertIsNone(result)


class TestCalculatePortfolioTaxes(unittest.TestCase):
    def test_calculate_portfolio_taxes_dict_and_object_deals(self):
        portfolio_id = "port_" + uuid.uuid4().hex
        user_id = "usr_" + uuid.uuid4().hex
        holding_period = random.randint(1, 365)
        dividends = round(random.uniform(10.0, 500.0), 2)

        price_dict_sell = round(random.uniform(120.0, 300.0), 2)
        shares_dict_sell = random.randint(2, 50)
        deal_dict_sell = {
            "type": "SELL",
            "price": price_dict_sell,
            "shares": shares_dict_sell,
        }

        price_dict_buy = round(random.uniform(80.0, 150.0), 2)
        shares_dict_buy = random.randint(2, 50)
        deal_dict_buy = {
            "type": "BUY",
            "price": price_dict_buy,
            "shares": shares_dict_buy,
        }

        price_obj_sell = round(random.uniform(110.0, 250.0), 2)
        shares_obj_sell = random.randint(2, 50)
        deal_obj_sell = types.SimpleNamespace(
            type="SELL", price=price_obj_sell, shares=shares_obj_sell
        )

        price_obj_hold = round(random.uniform(90.0, 200.0), 2)
        shares_obj_hold = random.randint(2, 50)
        deal_obj_hold = types.SimpleNamespace(
            type="HOLD", price=price_obj_hold, shares=shares_obj_hold
        )

        deals = [deal_dict_sell, deal_dict_buy, deal_obj_sell, deal_obj_hold]

        expected_profit = (price_dict_sell - 100.0) * shares_dict_sell + (
            price_obj_sell - 100.0
        ) * shares_obj_sell
        expected_tax = round(
            max(0.0, expected_profit * 0.13 + dividends * 0.13), 2
        )

        result = calculate_portfolio_taxes(
            portfolio_id=portfolio_id,
            user_id=user_id,
            deals=deals,
            holding_period=holding_period,
            dividends=dividends,
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["user_id"], user_id)
        self.assertEqual(result["total_tax_due"], expected_tax)

    def test_calculate_portfolio_taxes_loss_caps_at_zero(self):
        portfolio_id = "port_" + uuid.uuid4().hex
        user_id = "usr_" + uuid.uuid4().hex
        holding_period = random.randint(1, 365)
        dividends = 0.0

        heavy_loss_price = round(random.uniform(10.0, 30.0), 2)
        heavy_loss_shares = random.randint(500, 1000)
        deal_loss = {
            "type": "SELL",
            "price": heavy_loss_price,
            "shares": heavy_loss_shares,
        }

        result = calculate_portfolio_taxes(
            portfolio_id=portfolio_id,
            user_id=user_id,
            deals=[deal_loss],
            holding_period=holding_period,
            dividends=dividends,
        )

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["user_id"], user_id)
        self.assertEqual(result["total_tax_due"], 0.0)

    def test_calculate_portfolio_taxes_empty_deals(self):
        portfolio_id = "port_" + uuid.uuid4().hex
        user_id = "usr_" + uuid.uuid4().hex
        holding_period = random.randint(1, 365)
        dividends = round(random.uniform(50.0, 200.0), 2)

        expected_tax = round(max(0.0, dividends * 0.13), 2)

        result = calculate_portfolio_taxes(
            portfolio_id=portfolio_id,
            user_id=user_id,
            deals=[],
            holding_period=holding_period,
            dividends=dividends,
        )

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["user_id"], user_id)
        self.assertEqual(result["total_tax_due"], expected_tax)

    def test_calculate_portfolio_taxes_deal_missing_attributes_defaults(self):
        portfolio_id = "port_" + uuid.uuid4().hex
        user_id = "usr_" + uuid.uuid4().hex
        holding_period = random.randint(1, 365)
        dividends = 0.0

        deal_dict_incomplete = {"type": "SELL"}
        deal_obj_incomplete = types.SimpleNamespace(type="SELL")

        result = calculate_portfolio_taxes(
            portfolio_id=portfolio_id,
            user_id=user_id,
            deals=[deal_dict_incomplete, deal_obj_incomplete],
            holding_period=holding_period,
            dividends=dividends,
        )

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["user_id"], user_id)
        self.assertEqual(result["total_tax_due"], 0.0)


if __name__ == "__main__":
    unittest.main()