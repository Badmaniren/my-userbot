import unittest
from unittest.mock import patch
import random
import uuid
import io

from skills.market_portfolio_stress_resilience_matrix import (
    MatrixEvaluationError,
    StressResilienceMatrixCalculator,
    market_portfolio_stress_resilience_matrix
)

class TestMarketPortfolioStressResilienceMatrix(unittest.TestCase):

    def test_evaluate_resilience_success(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = uuid.uuid4().hex
        weight = round(random.uniform(0.1, 5.0), 2)
        health_base = round(random.uniform(50.0, 150.0), 2)
        resilience_index = round(random.uniform(10.0, 500.0), 2)
        status = uuid.uuid4().hex

        mock_db_data = {
            "weight": weight,
            "health_base": health_base
        }
        mock_exec_result = {
            "resilience_index": resilience_index,
            "status": status
        }

        with patch("skills.market_portfolio_stress_resilience_matrix.external_db_storage") as mock_db, \
             patch("skills.market_portfolio_stress_resilience_matrix.market_portfolio_stress_scenario_executor_bridge") as mock_bridge:

            mock_db.fetch_portfolio_matrix_params.return_value = mock_db_data
            mock_bridge.run_stress_matrix.return_value = mock_exec_result

            calculator = StressResilienceMatrixCalculator()
            result = calculator.evaluate_resilience(portfolio_id, scenario_code)

            mock_db.fetch_portfolio_matrix_params.assert_called_once_with(portfolio_id, scenario_code)
            mock_bridge.run_stress_matrix.assert_called_once_with(portfolio_id, scenario_code)

            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["scenario"], scenario_code)
            self.assertEqual(result["resilience_index"], resilience_index)
            self.assertEqual(result["status"], status)

    def test_evaluate_resilience_negative_weight_raises(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = uuid.uuid4().hex
        negative_weight = round(random.uniform(-10.0, -0.01), 2)

        mock_db_data = {
            "weight": negative_weight,
            "health_base": 100.0
        }

        with patch("skills.market_portfolio_stress_resilience_matrix.external_db_storage") as mock_db:
            mock_db.fetch_portfolio_matrix_params.return_value = mock_db_data

            calculator = StressResilienceMatrixCalculator()
            with self.assertRaises(MatrixEvaluationError):
                calculator.evaluate_resilience(portfolio_id, scenario_code)

    def test_process_stream_audit(self):
        random_chunk = bytes([random.randint(0, 255) for _ in range(32)])
        stream_obj = io.BytesIO(random_chunk)

        with patch("skills.market_portfolio_stress_resilience_matrix.market_portfolio_stress_audit_realtime_streamer") as mock_streamer:
            mock_streamer.export_stream_chunk.return_value = True

            calculator = StressResilienceMatrixCalculator()
            success = calculator.process_stream_audit(stream_obj)

            self.assertTrue(success)
            mock_streamer.export_stream_chunk.assert_called_once_with(random_chunk)

    def test_run_monte_carlo_stress(self):
        iterations = random.randint(10, 1000)
        volatility_factor = round(random.uniform(0.01, 1.0), 4)
        expected_paths = [{"path_id": uuid.uuid4().hex, "value": random.uniform(1.0, 100.0)} for _ in range(3)]

        with patch("skills.market_portfolio_stress_resilience_matrix.market_portfolio_stress_monte_carlo_engine") as mock_mc:
            mock_mc.simulate_matrix_paths.return_value = expected_paths

            calculator = StressResilienceMatrixCalculator()
            paths = calculator.run_monte_carlo_stress(iterations, volatility_factor)

            self.assertEqual(paths, expected_paths)
            mock_mc.simulate_matrix_paths.assert_called_once_with(iterations, volatility_factor)

    def test_market_portfolio_stress_resilience_matrix_wrapper(self):
        matrix_id = uuid.uuid4().hex
        portfolio_id = uuid.uuid4().hex
        initial_value = round(random.uniform(10000.0, 500000.0), 2)
        shock_factor = round(random.uniform(0.05, 0.5), 2)

        data = {
            "matrix_id": matrix_id,
            "portfolio_id": portfolio_id,
            "valuation_data": {
                "initial_value": initial_value
            },
            "simulation_data": {
                "shock_factor": shock_factor
            }
        }

        result = market_portfolio_stress_resilience_matrix(data)

        expected_score = round(initial_value * (1.0 - shock_factor), 2)

        self.assertEqual(result["matrix_id"], matrix_id)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["resilience_score"], expected_score)
        self.assertEqual(result["status"], "EVALUATED")

if __name__ == "__main__":
    unittest.main()