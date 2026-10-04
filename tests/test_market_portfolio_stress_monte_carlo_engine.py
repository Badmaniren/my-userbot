import unittest
from unittest.mock import patch
import random
import uuid

from skills import market_portfolio_stress_monte_carlo_engine
from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_audit_compliance_hub


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(1, 10)
        self.initial_value = round(random.uniform(50000.0, 150000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.4), 2)
        self.drift = round(random.uniform(-0.05, 0.05), 2)
        
        db_storage._in_memory_db = {
            self.portfolio_id: {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": self.volatility,
                "drift": self.drift
            }
        }
        
        self.engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()

    def test_run_simulation_returns_expected_structure(self):
        with patch.object(market_portfolio_audit_compliance_hub, "log_simulation") as mock_log:
            result = self.engine.run_simulation(
                portfolio_id=self.portfolio_id,
                simulations=self.simulations,
                horizon_days=self.horizon_days
            )

        self.assertIsInstance(result, dict)
        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertEqual(len(result["simulation_results"]), self.simulations)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["cvar_95"], float)
        mock_log.assert_called_once()

    def test_run_simulation_fallback_portfolio(self):
        unknown_id = f"unknown_{uuid.uuid4().hex[:8]}"
        sims = 10
        horizon = 5

        result = self.engine.run_simulation(
            portfolio_id=unknown_id,
            simulations=sims,
            horizon_days=horizon
        )

        self.assertEqual(result["portfolio_id"], unknown_id)
        self.assertEqual(len(result["simulation_results"]), sims)
        for path in result["simulation_results"]:
            self.assertEqual(len(path), horizon)

    def test_get_anomaly_adjustment_with_detector(self):
        random_multiplier = round(random.uniform(1.0, 5.0), 2)
        with patch.object(market_anomaly_detector, "get_current_anomaly_multiplier", return_value=random_multiplier):
            mult = self.engine._get_anomaly_adjustment()
            self.assertEqual(mult, random_multiplier)

    def test_get_anomaly_adjustment_fallback(self):
        with patch.object(market_anomaly_detector, "get_current_anomaly_multiplier", side_effect=AttributeError):
            mult = self.engine._get_anomaly_adjustment()
            self.assertEqual(mult, 1.0)

    def test_export_report_delegation(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(1000.0, 10000.0), 2)
        expected_ret = {"report_id": report_id, "loss_limit": loss_limit, "status": f"exported_{uuid.uuid4().hex[:4]}"}

        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_ret) as mock_export:
            res = self.engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res, expected_ret)

    def test_consume_stream_delegation(self):
        stream_data = {"stream_token": uuid.uuid4().hex}
        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=stream_data) as mock_stream:
            res = self.engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res, stream_data)

    def test_run_monte_carlo_stress_test_function(self):
        portfolio_val = round(random.uniform(10000.0, 500000.0), 2)
        iterations = random.randint(5, 30)
        scenario_params = {
            "volatility": round(random.uniform(0.15, 0.35), 2),
            "drift": round(random.uniform(-0.02, 0.02), 2),
            "horizon_days": random.randint(1, 7)
        }

        with patch.object(market_portfolio_audit_compliance_hub, "log_simulation") as mock_log:
            res = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
                portfolio_id=self.portfolio_id,
                portfolio_value=portfolio_val,
                scenario_params=scenario_params,
                iterations=iterations
            )

        self.assertIsInstance(res, dict)
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["initial_value"], portfolio_val)
        self.assertEqual(res["iterations"], iterations)
        self.assertIn("simulation_id", res)
        self.assertIn("var_95", res)
        self.assertIn("expected_shortfall", res)
        self.assertIsInstance(res["var_95"], float)
        self.assertIsInstance(res["expected_shortfall"], float)
        mock_log.assert_called_once()


if __name__ == "__main__":
    unittest.main()