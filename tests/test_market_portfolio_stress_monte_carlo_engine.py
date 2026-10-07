import unittest
from unittest.mock import patch
import uuid
import random

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)
from skills import db_storage


class TestMonteCarloStressEngine(unittest.TestCase):

    def test_monte_carlo_engine_simulation_and_invariants(self):
        portfolio_id = str(uuid.uuid4().hex)
        initial_val = round(random.uniform(50000.0, 500000.0), 2)
        vol = round(random.uniform(0.1, 0.4), 4)
        drift_val = round(random.uniform(-0.05, 0.05), 4)
        
        simulations_count = random.randint(100, 300)
        horizon = random.randint(5, 30)

        in_mem = getattr(db_storage, "_in_memory_db", None)
        if in_mem is None:
            in_mem = {}
            setattr(db_storage, "_in_memory_db", in_mem)
        
        in_mem[portfolio_id] = {
            "portfolio_id": portfolio_id,
            "initial_value": initial_val,
            "volatility": vol,
            "drift": drift_val
        }

        engine = MonteCarloStressEngine()
        result = engine.run_simulation(portfolio_id, simulations=simulations_count, horizon_days=horizon)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)

        self.assertEqual(len(result["simulation_results"]), simulations_count)
        for path in result["simulation_results"]:
            self.assertEqual(len(path), horizon)
            self.assertIsInstance(path[-1], float)

        self.assertGreaterEqual(result["cvar_95"], result["var_95"])

    def test_run_monte_carlo_stress_test_function(self):
        portfolio_id = str(uuid.uuid4().hex)
        portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        volatility = round(random.uniform(0.05, 0.5), 4)
        drift = round(random.uniform(-0.1, 0.1), 4)
        horizon_days = random.randint(1, 15)
        iterations = random.randint(50, 200)

        scenario_params = {
            "volatility": volatility,
            "drift": drift,
            "horizon_days": horizon_days
        }

        result = run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(result, dict)
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["initial_value"], portfolio_value)
        self.assertEqual(result["iterations"], iterations)
        self.assertIn("var_95", result)
        self.assertIn("expected_shortfall", result)
        self.assertGreaterEqual(result["expected_shortfall"], result["var_95"])

    def test_engine_export_and_stream(self):
        engine = MonteCarloStressEngine()
        report_id = str(uuid.uuid4().hex)
        loss_limit = round(random.uniform(1000.0, 50000.0), 2)

        export_res = engine.export_report(report_id, loss_limit)
        self.assertIsInstance(export_res, dict)
        self.assertEqual(export_res.get("report_id"), report_id)
        self.assertEqual(float(export_res.get("loss_limit")), float(loss_limit))

        stream_res = engine.consume_stream()
        self.assertTrue(stream_res is None or isinstance(stream_res, (dict, str, bytes)))


if __name__ == "__main__":
    unittest.main()