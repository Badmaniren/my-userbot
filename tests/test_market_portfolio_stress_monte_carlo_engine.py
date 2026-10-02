import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import math
import io

from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway
from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)


class TestMonteCarloStressEngine(unittest.TestCase):

    def test_run_simulation_with_fallback_db(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_val = float(random.randint(50000, 200000))
        simulations_count = random.randint(10, 50)
        horizon = random.randint(1, 5)

        with patch.object(db_storage, 'fetch_portfolio', side_effect=AttributeError):
            if not hasattr(db_storage, "_in_memory_db") or db_storage._in_memory_db is None:
                setattr(db_storage, "_in_memory_db", {})
            db_storage._in_memory_db[portfolio_id] = {
                "portfolio_id": portfolio_id,
                "initial_value": initial_val,
                "volatility": 0.15,
                "drift": 0.02
            }

            engine = MonteCarloStressEngine()
            result = engine.run_simulation(portfolio_id, simulations=simulations_count, horizon_days=horizon)

            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertEqual(len(result["simulation_results"]), simulations_count)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_run_simulation_with_anomaly_detector_mock(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_val = float(random.randint(10000, 50000))
        simulations_count = random.randint(5, 20)
        horizon = random.randint(1, 3)
        expected_multiplier = round(random.uniform(1.1, 3.0), 2)

        mock_db_data = {
            "portfolio_id": portfolio_id,
            "initial_value": initial_val,
            "volatility": 0.1,
            "drift": 0.01
        }

        with patch.object(db_storage, 'fetch_portfolio', return_value=mock_db_data):
            with patch('skills.market_anomaly_detector.get_current_anomaly_multiplier', return_value=expected_multiplier):
                engine = MonteCarloStressEngine()
                result = engine.run_simulation(portfolio_id, simulations=simulations_count, horizon_days=horizon)

                self.assertEqual(result["portfolio_id"], portfolio_id)
                self.assertGreaterEqual(result["var_95"], 0.0)
                self.assertGreaterEqual(result["cvar_95"], 0.0)

    def test_export_report_fallback(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = float(random.randint(1000, 9000))

        with patch.object(market_portfolio_data_exporter, 'export', side_effect=AttributeError):
            engine = MonteCarloStressEngine()
            res = engine.export_report(report_id, loss_limit)
            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

    def test_consume_stream_fallback(self):
        with patch.object(market_portfolio_api_gateway, 'stream_payload', side_effect=AttributeError):
            engine = MonteCarloStressEngine()
            res = engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_function(self):
        portfolio_id = f"target_{uuid.uuid4().hex[:8]}"
        portfolio_value = float(random.randint(100000, 500000))
        iterations = random.randint(20, 100)
        vol = round(random.uniform(0.1, 0.4), 2)
        drift_val = round(random.uniform(-0.05, 0.05), 4)
        horizon = random.randint(1, 10)

        scenario_params = {
            "volatility": vol,
            "drift": drift_val,
            "horizon_days": horizon
        }

        res = run_monte_carlo_stress_test(portfolio_id, portfolio_value, scenario_params, iterations)

        self.assertEqual(res["portfolio_id"], portfolio_id)
        self.assertEqual(res["initial_value"], portfolio_value)
        self.assertEqual(res["iterations"], iterations)
        self.assertIn("simulation_id", res)
        self.assertTrue(res["simulation_id"].startswith("sim_"))
        self.assertIsInstance(res["var_95"], float)
        self.assertIsInstance(res["expected_shortfall"], float)

    def test_stream_payload_with_bytes_io(self):
        random_bytes = f"payload_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)

        with patch.object(market_portfolio_api_gateway, 'stream_payload', return_value=mock_stream):
            engine = MonteCarloStressEngine()
            stream_result = engine.consume_stream()
            self.assertIsNotNone(stream_result)
            content = stream_result.read()
            self.assertEqual(content, random_bytes)


if __name__ == '__main__':
    unittest.main()