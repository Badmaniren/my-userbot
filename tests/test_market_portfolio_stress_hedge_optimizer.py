import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import io

from skills.market_portfolio_stress_hedge_optimizer import (
    optimize_stress_hedge,
    calculate_hedge_positions,
    validate_portfolio_liquidity,
    market_portfolio_stress_hedge_optimizer
)

class TestMarketPortfolioStressHedgeOptimizer(unittest.TestCase):

    def test_optimize_stress_hedge_success(self):
        portfolio_id = str(uuid.uuid4())
        stress_matrix_id = str(uuid.uuid4())
        risk_tolerance = round(random.uniform(0.05, 0.5), 2)
        expected_hedge = f"ASSET_{uuid.uuid4().hex[:6]}"
        available_cash = round(random.uniform(1000.0, 50000.0), 2)

        mock_evaluator = MagicMock()
        mock_evaluator.evaluate_matrix.return_value = {'recommended_hedge': expected_hedge}

        mock_liquidity = MagicMock()
        mock_liquidity.get_liquidity_profile.return_value = {'available_cash': available_cash}

        mock_db = MagicMock()

        with patch('skills.market_portfolio_stress_hedge_optimizer.market_portfolio_stress_scenario_matrix_evaluator', mock_evaluator), \
             patch('skills.market_portfolio_stress_hedge_optimizer.market_portfolio_liquidity_scenario_analyzer', mock_liquidity), \
             patch('skills.market_portfolio_stress_hedge_optimizer.db_storage', mock_db):

            result = optimize_stress_hedge(portfolio_id, stress_matrix_id, risk_tolerance)

            self.assertIn('hedge_recommendations', result)
            self.assertEqual(result['hedge_recommendations']['asset'], expected_hedge)
            self.assertEqual(result['hedge_recommendations']['volume'], available_cash * risk_tolerance)
            mock_db.log_operation.assert_called_once()

    def test_calculate_hedge_positions(self):
        portfolio_id = str(uuid.uuid4())
        liquidity_limit = round(random.uniform(500.0, 10000.0), 2)
        random_bytes = uuid.uuid4().bytes

        mock_collector = MagicMock()
        mock_collector.fetch_stream.return_value = io.BytesIO(random_bytes)

        with patch('skills.market_portfolio_stress_hedge_optimizer.market_portfolio_collector_agent', mock_collector):
            positions = calculate_hedge_positions(portfolio_id, liquidity_limit)

            self.assertIsInstance(positions, list)
            self.assertTrue(len(positions) > 0)
            self.assertEqual(positions[0]['amount'], liquidity_limit * 0.1)

    def test_validate_portfolio_liquidity(self):
        portfolio_id = str(uuid.uuid4())
        threshold = round(random.uniform(0.1, 0.9), 2)
        expected_response = {"status": "ok", "id": portfolio_id}

        mock_gateway = MagicMock()
        mock_gateway.send_request.return_value = expected_response

        with patch('skills.market_portfolio_stress_hedge_optimizer.market_portfolio_api_gateway', mock_gateway):
            response = validate_portfolio_liquidity(portfolio_id, threshold)

            self.assertEqual(response, expected_response)
            mock_gateway.send_request.assert_called_once_with(
                endpoint="/liquidity/check",
                params={"id": portfolio_id, "threshold": threshold}
            )

    def test_market_portfolio_stress_hedge_optimizer_interface(self):
        portfolio_id = str(uuid.uuid4())
        scenario_id = str(uuid.uuid4())
        target_risk = round(random.uniform(0.1, 0.4), 2)

        payload = {
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            "target_risk_reduction": target_risk
        }

        with patch('skills.market_portfolio_stress_hedge_optimizer.optimize_stress_hedge') as mock_optimize:
            result = market_portfolio_stress_hedge_optimizer(payload)

            self.assertIn("hedge_positions", result)
            self.assertIn("estimated_cost", result)
            self.assertEqual(result["status"], "optimized")
            self.assertEqual(result["hedge_positions"][0]["size"], target_risk * 1000)
            mock_optimize.assert_called_once_with(portfolio_id, scenario_id, target_risk)