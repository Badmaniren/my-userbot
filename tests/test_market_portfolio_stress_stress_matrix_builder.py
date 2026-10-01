import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import os

from skills.market_portfolio_stress_stress_matrix_builder import (
    start_new,
    market_portfolio_stress_stress_matrix_builder
)

class TestMarketPortfolioStressStressMatrixBuilder(unittest.TestCase):

    def test_start_new_basic_execution(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        liquidity_shock_factor = random.uniform(0.01, 0.99)

        mock_db = MagicMock()
        mock_db.read_stream.return_value = None

        mock_mc = MagicMock()
        mock_mc.run.return_value = None

        mock_sim = MagicMock()
        sim_data_key = f"key_{uuid.uuid4().hex[:6]}"
        sim_data_val = random.randint(100, 999)
        mock_sim.simulate.return_value = {sim_data_key: sim_data_val}

        result = start_new(
            portfolio_id=portfolio_id,
            liquidity_shock_factor=liquidity_shock_factor,
            db_storage=mock_db,
            market_portfolio_stress_monte_carlo_engine=mock_mc,
            market_portfolio_scenario_simulator=mock_sim
        )

        self.assertIn("matrix_id", result)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertIn("simulation_data", result)
        self.assertEqual(result["simulation_data"].get(sim_data_key), sim_data_val)
        
        mock_db.read_stream.assert_called_once()
        mock_mc.run.assert_called_once()
        mock_sim.simulate.assert_called_once()

    def test_start_new_missing_dependencies(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        result = start_new(portfolio_id=portfolio_id)
        self.assertIn("matrix_id", result)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["simulation_data"], {})

    def test_market_portfolio_stress_stress_matrix_builder_facade(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        output_target = f"matrix_out_{uuid.uuid4().hex[:8]}.json"
        
        builder_input = {
            "portfolio_id": portfolio_id,
            "output_target": output_target
        }

        mock_storage_func = MagicMock()

        with patch("skills.db_storage.db_storage", mock_storage_func, create=True):
            try:
                result = market_portfolio_stress_stress_matrix_builder(builder_input)
            finally:
                if os.path.exists(output_target):
                    os.remove(output_target)

        self.assertIn("matrix_id", result)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["output_path"], output_target)
        self.assertTrue(os.path.exists(output_target))

        mock_storage_func.assert_called_once()
        call_arg = mock_storage_func.call_args[0][0]
        self.assertEqual(call_arg.get("action"), "save")
        self.assertEqual(call_arg.get("table"), "stress_matrices")
        self.assertEqual(call_arg.get("portfolio_id"), portfolio_id)
        self.assertEqual(call_arg.get("matrix_id"), result["matrix_id"])