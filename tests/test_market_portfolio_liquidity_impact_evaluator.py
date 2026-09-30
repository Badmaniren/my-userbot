import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid

from skills.market_portfolio_liquidity_impact_evaluator import (
    MarketPortfolioLiquidityImpactEvaluator,
    market_portfolio_liquidity_impact_evaluator
)


class TestMarketPortfolioLiquidityImpactEvaluator(unittest.TestCase):

    def test_evaluator_initialization_and_dependencies(self):
        rand_db = MagicMock()
        rand_tool1 = MagicMock()
        rand_tool2 = MagicMock()
        rand_anomaly = MagicMock()
        rand_slippage = MagicMock()

        evaluator = MarketPortfolioLiquidityImpactEvaluator(
            db_storage=rand_db,
            extractor_tool_1790087207=rand_tool1,
            extractor_tool_1790102839=rand_tool2,
            market_anomaly_detector=rand_anomaly,
            market_portfolio_slippage_model=rand_slippage
        )

        self.assertEqual(evaluator.db_storage, rand_db)
        self.assertEqual(evaluator.extractor_tool_1, rand_tool1)
        self.assertEqual(evaluator.extractor_tool_2, rand_tool2)
        self.assertEqual(evaluator.market_anomaly_detector, rand_anomaly)
        self.assertEqual(evaluator.market_portfolio_slippage_model, rand_slippage)

    def test_evaluate_impact_logic(self):
        rand_token = f"TOKEN_{uuid.uuid4().hex[:6].upper()}"
        rand_size = round(random.uniform(100.0, 50000.0), 2)

        mock_db = MagicMock()
        evaluator = MarketPortfolioLiquidityImpactEvaluator(db_storage=mock_db)

        result = evaluator.evaluate_impact(token=rand_token, order_size=rand_size)

        self.assertIn("id", result)
        self.assertEqual(result["token"], rand_token)
        self.assertAlmostEqual(result["impact"], rand_size * 0.00001)
        mock_db.save.assert_called_once_with(result)

    def test_parse_liquidity_stream(self):
        rand_payload = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(rand_payload)

        evaluator = MarketPortfolioLiquidityImpactEvaluator()
        res = evaluator.parse_liquidity_stream(stream)

        self.assertEqual(res["status"], "parsed")
        self.assertEqual(res["data_size"], len(rand_payload))

    def test_detect_price_failure_zones(self):
        rand_threshold = round(random.uniform(1.0, 100.0), 2)
        evaluator = MarketPortfolioLiquidityImpactEvaluator()
        zones = evaluator.detect_price_failure_zones(threshold=rand_threshold)

        self.assertIsInstance(zones, list)
        self.assertTrue(len(zones) > 0)
        self.assertEqual(zones[0]["threshold"], rand_threshold)
        self.assertIn("zone_id", zones[0])

    def test_calculate_execution_penalty(self):
        rand_tx_id = f"tx_{uuid.uuid4().hex[:8]}"
        rand_size = round(random.uniform(500.0, 100000.0), 2)

        evaluator = MarketPortfolioLiquidityImpactEvaluator()
        penalty = evaluator.calculate_execution_penalty(transaction_id=rand_tx_id, order_size=rand_size)

        self.assertEqual(penalty["transaction_id"], rand_tx_id)
        self.assertAlmostEqual(penalty["estimated_cost"], rand_size * 0.0015)

    def test_functional_wrapper_with_collected_data(self):
        rand_portfolio_id = f"port_{uuid.uuid4().hex[:6]}"
        rand_symbol = f"SYM_{uuid.uuid4().hex[:4].upper()}"
        rand_volume = round(random.uniform(1000.0, 75000.0), 2)
        rand_collected = {"status": "ok", "liquidity_depth": random.randint(10, 100)}

        payload = {
            "portfolio_id": rand_portfolio_id,
            "asset_symbol": rand_symbol,
            "order_volume": rand_volume,
            "collected_market_data": rand_collected
        }

        with patch("skills.market_portfolio_liquidity_impact_evaluator.db_storage") as mock_db_func:
            result = market_portfolio_liquidity_impact_evaluator(payload)

            self.assertEqual(result["portfolio_id"], rand_portfolio_id)
            self.assertEqual(result["asset_symbol"], rand_symbol)
            self.assertEqual(result["order_volume"], rand_volume)
            self.assertEqual(result["collected_market_data"], rand_collected)
            self.assertEqual(result["status"], "evaluated")
            self.assertAlmostEqual(result["impact_score"], round(rand_volume * 0.00002, 4))
            mock_db_func.assert_called_once()

    def test_functional_wrapper_without_collected_data(self):
        rand_portfolio_id = f"port_{uuid.uuid4().hex[:6]}"
        rand_symbol = f"SYM_{uuid.uuid4().hex[:4].upper()}"
        rand_volume = round(random.uniform(2000.0, 50000.0), 2)
        mock_collected_output = {"auto_collected": True, "metric": random.random()}

        payload = {
            "portfolio_id": rand_portfolio_id,
            "asset_symbol": rand_symbol,
            "order_volume": rand_volume
        }

        with patch("skills.market_portfolio_liquidity_impact_evaluator.market_portfolio_collector_agent") as mock_collector, \
             patch("skills.market_portfolio_liquidity_impact_evaluator.db_storage") as mock_db_func:

            mock_collector.return_value = mock_collected_output
            result = market_portfolio_liquidity_impact_evaluator(payload)

            mock_collector.assert_called_once_with({
                "portfolio_id": rand_portfolio_id,
                "symbol": rand_symbol,
                "volume": rand_volume
            })
            self.assertEqual(result["collected_market_data"], mock_collected_output)
            self.assertEqual(result["status"], "evaluated")
            mock_db_func.assert_called_once()