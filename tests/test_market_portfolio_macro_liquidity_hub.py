import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import datetime
import io
from skills.market_portfolio_macro_liquidity_hub import start_new, market_portfolio_macro_liquidity_hub

class TestMarketPortfolioMacroLiquidityHub(unittest.TestCase):

    def test_start_new_with_valid_mocks(self):
        rand_parsed_val = uuid.uuid4().hex

        market_parser_mock = MagicMock()
        market_parser_mock.parse.return_value = rand_parsed_val

        extractor_mock = MagicMock()
        db_storage_mock = MagicMock()

        res = start_new(
            market_parser=market_parser_mock,
            extractor_tool_1790087207=extractor_mock,
            db_storage=db_storage_mock
        )

        market_parser_mock.parse.assert_called_once()
        extractor_mock.extract.assert_called_once()
        db_storage_mock.query.assert_called_once()
        self.assertEqual(res, rand_parsed_val)

    def test_start_new_without_objects(self):
        res = start_new()
        self.assertIsNone(res)

    def test_hub_aggregate_and_sync_with_record(self):
        portfolio_id = uuid.uuid4().hex
        rand_liquidity = round(random.uniform(1.0, 100.0), 2)
        rand_volume = random.randint(1000, 999999)

        db_mock = MagicMock()
        db_mock.get_record.return_value = {
            "liquidity_factor": rand_liquidity,
            "aggregate_volume": rand_volume
        }

        hub = market_portfolio_macro_liquidity_hub(db=db_mock)
        result = hub.aggregate_and_sync(portfolio_id)

        db_mock.get_record.assert_called_once_with(portfolio_id)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["liquidity_factor"], rand_liquidity)
        self.assertEqual(result["aggregate_volume"], rand_volume)

    def test_hub_aggregate_and_sync_without_record(self):
        portfolio_id = uuid.uuid4().hex
        db_mock = MagicMock()
        db_mock.get_record.return_value = None

        hub = market_portfolio_macro_liquidity_hub(db=db_mock)
        result = hub.aggregate_and_sync(portfolio_id)

        db_mock.get_record.assert_called_once_with(portfolio_id)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["liquidity_factor"], 0.0)
        self.assertEqual(result["aggregate_volume"], 0)

if __name__ == '__main__':
    unittest.main()