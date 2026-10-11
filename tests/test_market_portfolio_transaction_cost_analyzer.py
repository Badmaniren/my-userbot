import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.market_portfolio_transaction_cost_analyzer import (
    market_portfolio_transaction_cost_analyzer,
    start_new
)

class TestMarketPortfolioTransactionCostAnalyzer(unittest.TestCase):

    def test_start_new_invalid_deps_raises_type_error(self):
        rand_invalid = random.choice([
            uuid.uuid4().hex,
            random.randint(100, 999),
            [uuid.uuid4().hex, 123],
            None,
            123.45
        ])
        with self.assertRaises(TypeError):
            start_new(rand_invalid)

    def test_start_new_default_flow(self):
        deps = {}
        res = start_new(deps)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("status"), "success")
        self.assertIn("portfolio_id", res)
        self.assertEqual(res.get("calculated_fee"), 0.001)
        self.assertEqual(res.get("spread"), 0.05)

    def test_start_new_with_db_fetching(self):
        expected_portfolio_id = uuid.uuid4().hex
        mock_db = MagicMock()
        mock_db.fetch_portfolio.return_value = {"id": expected_portfolio_id}

        deps = {
            "db_storage": mock_db
        }
        res = start_new(deps)
        mock_db.fetch_portfolio.assert_called_once()
        self.assertEqual(res.get("portfolio_id"), expected_portfolio_id)

    def test_start_new_with_anomaly_detector_and_parser(self):
        mock_anomaly = MagicMock()
        mock_parser = MagicMock()

        deps = {
            "market_anomaly_detector": mock_anomaly,
            "market_parser": mock_parser
        }
        res = start_new(deps)
        mock_anomaly.scan.assert_called_once()
        mock_parser.parse_stream.assert_called_once()
        self.assertEqual(res.get("status"), "success")

    def test_start_new_with_slippage_model(self):
        expected_res = {
            "status": "success",
            "estimated_slippage": random.uniform(0.001, 0.05),
            "random_marker": uuid.uuid4().hex
        }
        mock_slippage = MagicMock()
        mock_slippage.estimate.return_value = expected_res

        deps = {
            "market_portfolio_slippage_model": mock_slippage
        }
        res = start_new(deps)
        mock_slippage.estimate.assert_called_once()
        self.assertEqual(res, expected_res)

    def test_start_new_with_execution_cost_optimizer(self):
        expected_res = {
            "status": "success",
            "optimized": True,
            "uuid": uuid.uuid4().hex
        }
        mock_optimizer = MagicMock()
        mock_optimizer.analyze.return_value = expected_res

        deps = {
            "market_portfolio_execution_cost_optimizer": mock_optimizer
        }
        res = start_new(deps)
        mock_optimizer.analyze.assert_called_once()
        self.assertEqual(res, expected_res)

    def test_market_portfolio_transaction_cost_analyzer_basic(self):
        portfolio_id = uuid.uuid4().hex
        ticker = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=4))
        volume = random.uniform(100.0, 10000.0)
        exchange_fee_rate = random.uniform(0.0001, 0.005)
        slippage_metrics = {}
        liquidity_data = {"depth": random.randint(10, 100)}

        res = market_portfolio_transaction_cost_analyzer(
            portfolio_id=portfolio_id,
            ticker=ticker,
            volume=volume,
            exchange_fee_rate=exchange_fee_rate,
            slippage_metrics=slippage_metrics,
            liquidity_data=liquidity_data
        )

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["portfolio_id"], portfolio_id)
        self.assertEqual(res["ticker"], ticker)
        self.assertEqual(res["volume"], volume)
        self.assertEqual(res["exchange_fee_rate"], exchange_fee_rate)
        self.assertIn("total_transaction_cost", res)
        self.assertIn("impact_on_portfolio_return", res)
        self.assertEqual(res["liquidity_info"], str(liquidity_data))

    def test_market_portfolio_transaction_cost_analyzer_with_slippage_dict(self):
        portfolio_id = uuid.uuid4().hex
        ticker = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=3))
        volume = random.uniform(500.0, 5000.0)
        exchange_fee_rate = 0.002
        est_slip = random.uniform(0.001, 0.02)
        tot_cost = random.uniform(10.0, 100.0)

        slippage_metrics = {
            "estimated_slippage": est_slip,
            "total_cost": tot_cost
        }
        liquidity_data = uuid.uuid4().hex

        res = market_portfolio_transaction_cost_analyzer(
            portfolio_id=portfolio_id,
            ticker=ticker,
            volume=volume,
            exchange_fee_rate=exchange_fee_rate,
            slippage_metrics=slippage_metrics,
            liquidity_data=liquidity_data
        )

        expected_total_transaction_cost = tot_cost + (volume * est_slip)
        expected_impact = - (expected_total_transaction_cost / max(volume, 1.0))

        self.assertEqual(res["total_transaction_cost"], expected_total_transaction_cost)
        self.assertEqual(res["impact_on_portfolio_return"], expected_impact)
        self.assertEqual(res["liquidity_info"], str(liquidity_data))