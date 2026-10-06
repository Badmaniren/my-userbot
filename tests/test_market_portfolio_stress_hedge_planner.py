import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_stress_hedge_planner import (
    plan_portfolio_hedge,
    MarketPortfolioStressHedgePlanner
)

class TestMarketPortfolioStressHedgePlanner(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.historical_window = random.randint(10, 365)
        self.asset = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.volume = round(random.uniform(100.0, 10000.0), 2)
        self.ticker = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.slippage = round(random.uniform(0.0001, 0.05), 4)
        self.scenario_token = uuid.uuid4().hex
        self.threshold = round(random.uniform(0.1, 0.9), 2)

    def test_composition_integration_and_hedge_planning(self):
        expected_matrix_result = {
            uuid.uuid4().hex: random.choice([True, False]),
            "max_drawdown": round(random.uniform(0.05, 0.5), 2),
            "asset": self.asset,
            "recommended_volume": self.volume
        }

        expected_optimization_result = {
            "optimized_cost": round(random.uniform(10.0, 500.0), 2),
            "routing_status": "success",
            "order_id": uuid.uuid4().hex
        }

        with patch("skills.market_portfolio_stress_scenario_matrix_evaluator.MarketPortfolioStressScenarioMatrixEvaluator") as mock_evaluator_cls, \
             patch("skills.market_portfolio_execution_cost_optimizer.MarketPortfolioExecutionCostOptimizer") as mock_optimizer_cls:

            mock_evaluator_instance = mock_evaluator_cls.return_value
            mock_evaluator_instance.evaluate_matrix.return_value = expected_matrix_result

            mock_optimizer_instance = mock_optimizer_cls.return_value
            mock_optimizer_instance.optimize_execution_cost.return_value = expected_optimization_result

            planner = MarketPortfolioStressHedgePlanner()
            result = planner.execute_hedge_plan(
                portfolio_id=self.portfolio_id,
                historical_window=self.historical_window,
                asset=self.asset,
                volume=self.volume,
                ticker=self.ticker,
                slippage_model_output=self.slippage
            )

            mock_evaluator_instance.evaluate_matrix.assert_called_once_with(
                self.portfolio_id, self.historical_window
            )
            mock_optimizer_instance.optimize_execution_cost.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                asset=self.asset,
                volume=self.volume,
                ticker=self.ticker,
                slippage_model_output=self.slippage
            )

            self.assertIn("stress_matrix", result)
            self.assertIn("execution_optimization", result)
            self.assertEqual(result["stress_matrix"], expected_matrix_result)
            self.assertEqual(result["execution_optimization"], expected_optimization_result)

    def test_functional_wrapper_plan_portfolio_hedge(self):
        mock_matrix = {uuid.uuid4().hex: random.randint(1, 100)}
        mock_opt = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_scenario_matrix_evaluator.evaluate_stress_scenario_matrix") as mock_eval_func, \
             patch("skills.market_portfolio_execution_cost_optimizer.market_portfolio_execution_cost_optimizer") as mock_opt_func:

            mock_eval_func.return_value = mock_matrix
            mock_opt_func.return_value = mock_opt

            payload = {
                "portfolio_id": self.portfolio_id,
                "historical_window": self.historical_window,
                "ticker": self.ticker,
                "volume": self.volume,
                "slippage_model_output": self.slippage
            }

            response = plan_portfolio_hedge(payload)

            self.assertIsInstance(response, dict)
            self.assertEqual(response.get("matrix_evaluation"), mock_matrix)
            self.assertEqual(response.get("cost_optimization"), mock_opt)

    def test_hedge_planner_anomaly_handling(self):
        with patch("skills.market_portfolio_stress_scenario_matrix_evaluator.MarketPortfolioStressScenarioMatrixEvaluator") as mock_evaluator_cls:
            mock_evaluator_instance = mock_evaluator_cls.return_value
            anomaly_detected = random.choice([True, False])
            mock_evaluator_instance.detect_matrix_anomalies.return_value = anomaly_detected

            planner = MarketPortfolioStressHedgePlanner()
            result = planner.check_anomalies(self.scenario_token, self.threshold)

            mock_evaluator_instance.detect_matrix_anomalies.assert_called_once_with(
                self.scenario_token, self.threshold
            )
            self.assertEqual(result, anomaly_detected)

    def test_stream_matrix_evaluation_integration(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)
        expected_stream_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_scenario_matrix_evaluator.MarketPortfolioStressScenarioMatrixEvaluator") as mock_evaluator_cls:
            mock_evaluator_instance = mock_evaluator_cls.return_value
            mock_evaluator_instance.evaluate_stream_matrix.return_value = expected_stream_result

            planner = MarketPortfolioStressHedgePlanner()
            res = planner.evaluate_stream(self.portfolio_id, stream_data)

            mock_evaluator_instance.evaluate_stream_matrix.assert_called_once_with(
                self.portfolio_id, stream_data
            )
            self.assertEqual(res, expected_stream_result)

if __name__ == '__main__':
    unittest.main()