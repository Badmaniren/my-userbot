import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import requests

from skills.market_portfolio_multi_exchange_arb_detector import start_new, market_portfolio_multi_exchange_arb_detector


class TestMarketPortfolioMultiExchangeArbDetector(unittest.TestCase):

    def setUp(self):
        self.rand_symbol = f"COIN-{uuid.uuid4().hex[:4].upper()}"
        self.rand_exchanges = [uuid.uuid4().hex, uuid.uuid4().hex]
        self.rand_run_id = uuid.uuid4().hex

    @patch('skills.market_portfolio_multi_exchange_arb_detector.requests.get')
    def test_start_new_with_all_mocks(self, mock_requests_get):
        mock_parser = MagicMock()
        mock_detector = MagicMock()
        mock_extractor = MagicMock()

        mock_deps = {
            "market_parser": mock_parser,
            "market_anomaly_detector": mock_detector,
            "extractor_tool_1790087207": mock_extractor
        }

        mock_response = MagicMock()
        mock_requests_get.return_value = mock_response

        result = start_new(mock_deps)

        mock_parser.fetch_ticker.assert_called_once()
        mock_detector.detect.assert_called_once()
        mock_extractor.read_stream.assert_called_once()
        mock_requests_get.assert_called_once()

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "ok")
        self.assertEqual(result.get("arbitrage_index"), 100.0)

    @patch('skills.market_portfolio_multi_exchange_arb_detector.requests.get')
    def test_start_new_with_empty_mocks(self, mock_requests_get):
        mock_deps = {}
        mock_response = MagicMock()
        mock_requests_get.return_value = mock_response

        result = start_new(mock_deps)

        mock_requests_get.assert_called_once()
        self.assertEqual(result, {"status": "ok", "arbitrage_index": 100.0})

    def test_market_portfolio_multi_exchange_arb_detector_btc_usd(self):
        arb_input = {
            "run_id": self.rand_run_id,
            "symbol": "BTC-USD",
            "min_spread_threshold": random.uniform(10.0, 50.0),
            "exchanges_to_scan": self.rand_exchanges
        }

        result = market_portfolio_multi_exchange_arb_detector(arb_input)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("execution_path"), "direct_arbitrage_pipeline")
        opportunities = result.get("opportunities")
        self.assertIsInstance(opportunities, list)
        self.assertEqual(len(opportunities), 1)

        opp = opportunities[0]
        self.assertEqual(opp.get("symbol"), "BTC-USD")
        self.assertEqual(opp.get("buy_exchange"), self.rand_exchanges[0])
        self.assertEqual(opp.get("sell_exchange"), self.rand_exchanges[1])
        self.assertEqual(opp.get("spread"), 150.0)

    def test_market_portfolio_multi_exchange_arb_detector_generic_symbol(self):
        arb_input = {
            "run_id": self.rand_run_id,
            "symbol": self.rand_symbol,
            "min_spread_threshold": random.uniform(1.0, 10.0),
            "exchanges_to_scan": self.rand_exchanges
        }

        result = market_portfolio_multi_exchange_arb_detector(arb_input)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("execution_path"), "direct_arbitrage_pipeline")
        opportunities = result.get("opportunities")
        self.assertIsInstance(opportunities, list)
        self.assertEqual(len(opportunities), 1)

        opp = opportunities[0]
        self.assertEqual(opp.get("symbol"), self.rand_symbol)
        self.assertEqual(opp.get("buy_exchange"), self.rand_exchanges[0])
        self.assertEqual(opp.get("sell_exchange"), self.rand_exchanges[1])
        self.assertEqual(opp.get("spread"), 100.0)

    def test_market_portfolio_multi_exchange_arb_detector_insufficient_exchanges(self):
        arb_input = {
            "run_id": self.rand_run_id,
            "symbol": self.rand_symbol,
            "min_spread_threshold": 5.0,
            "exchanges_to_scan": [self.rand_exchanges[0]]
        }

        result = market_portfolio_multi_exchange_arb_detector(arb_input)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("opportunities"), [])
        self.assertEqual(result.get("execution_path"), "direct_arbitrage_pipeline")


if __name__ == '__main__':
    unittest.main()