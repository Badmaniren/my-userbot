import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import math
import io

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)


class TestMonteCarloStressEngine(unittest.TestCase):

    def test_run_simulation_success(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        initial_value = round(random.uniform(10000.0, 500000.0), 2)
        simulations = random.randint(10, 50)
        horizon_days = random.randint(1, 30)

        mock_portfolio_data = {
            "portfolio_id": portfolio_id,
            "initial_value": initial_value,
            "volatility": 0.15,
            "drift": 0.05
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio_data) as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.1) as mock_anomaly:
            
            engine = MonteCarloStressEngine()
            result = engine.run_simulation(portfolio_id, simulations, horizon_days)

            mock_fetch.assert_called_once_with(portfolio_id)
            mock_anomaly.assert_called_once()

            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertEqual(len(result["simulation_results"]), simulations)
            for path in result["simulation_results"]:
                self.assertEqual(len(path), horizon_days)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_run_simulation_fallback_db(self):
        portfolio_id = f"port_fb_{uuid.uuid4().hex}"
        simulations = random.randint(5, 20)
        horizon_days = random.randint(1, 10)

        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError("No fetch")):
            with patch.object(db_storage_mock := type("Obj", (), {}), "_in_memory_db", {portfolio_id: {"initial_value": 50000.0}}):
                with patch("skills.market_portfolio_stress_monte_carlo_engine.db_storage", db_storage_mock):
                    engine = MonteCarloStressEngine()
                    result = engine.run_simulation(portfolio_id, simulations, horizon_days)
                    self.assertEqual(result["portfolio_id"], portfolio_id)
                    self.assertEqual(len(result["simulation_results"]), simulations)

    def test_get_anomaly_adjustment_exception(self):
        engine = MonteCarloStressEngine()
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError("No method")):
            mult = engine._get_anomaly_adjustment()
            self.assertEqual(mult, 1.0)

    def test_export_report(self):
        report_id = f"rep_{uuid.uuid4().hex}"
        loss_limit = round(random.uniform(1000.0, 50000.0), 2)
        expected_dict = {"report_id": report_id, "loss_limit": loss_limit, "status": "exported"}

        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_dict) as mock_export:
            engine = MonteCarloStressEngine()
            res = engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res, expected_dict)

    def test_export_report_exception(self):
        report_id = f"rep_err_{uuid.uuid4().hex}"
        loss_limit = round(random.uniform(100.0, 1000.0), 2)

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError("No export")):
            engine = MonteCarloStressEngine()
            res = engine.export_report(report_id, loss_limit)
            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

    def test_consume_stream(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=stream_data) as mock_stream:
            engine = MonteCarloStressEngine()
            res = engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res, stream_data)

    def test_consume_stream_exception(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError("No stream")):
            engine = MonteCarloStressEngine()
            res = engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_function(self):
        portfolio_id = f"func_port_{uuid.uuid4().hex}"
        portfolio_value = round(random.uniform(50000.0, 1000000.0), 2)
        iterations = random.randint(20, 100)
        scenario_params = {
            "volatility": round(random.uniform(0.1, 0.5), 2),
            "drift": round(random.uniform(-0.05, 0.05), 4),
            "horizon_days": random.randint(1, 15)
        }

        result = run_monte_carlo_stress_test(portfolio_id, portfolio_value, scenario_params, iterations)

        self.assertIn("simulation_id", result)
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["initial_value"], portfolio_value)
        self.assertEqual(result["iterations"], iterations)
        self.assertIn("var_95", result)
        self.assertIn("expected_shortfall", result)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()