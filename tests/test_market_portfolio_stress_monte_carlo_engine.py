import unittest
from unittest.mock import patch
import uuid
import random
import math
import io

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.engine = MonteCarloStressEngine()
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(5, 15)
        self.loss_limit = round(random.uniform(1000.0, 50000.0), 2)
        self.report_id = f"rep_{uuid.uuid4().hex[:8]}"

    def test_run_simulation_success(self):
        mock_data = {
            "portfolio_id": self.portfolio_id,
            "initial_value": round(random.uniform(50000.0, 200000.0), 2),
            "volatility": round(random.uniform(0.1, 0.4), 4),
            "drift": round(random.uniform(-0.05, 0.05), 4)
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_data) as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0) as mock_anomaly, \
             patch("skills.market_portfolio_audit_compliance_hub") as mock_audit:

            result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

            mock_fetch.assert_called_once_with(self.portfolio_id)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations)

    def test_run_simulation_missing_fetch_attribute(self):
        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError), \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0):

            with patch.object(db_storage, "_in_memory_db", {self.portfolio_id: {"initial_value": 123456.0}}, create=True):
                result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)
                self.assertEqual(result["portfolio_id"], self.portfolio_id)
                self.assertIsInstance(result["var_95"], float)

    def test_get_anomaly_adjustment_with_exception(self):
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError):
            mult = self.engine._get_anomaly_adjustment()
            self.assertEqual(mult, 1.0)

    def test_export_report_success(self):
        expected_dict = {"report_id": self.report_id, "loss_limit": self.loss_limit, "status": "exported"}
        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_dict) as mock_export:
            res = self.engine.export_report(self.report_id, self.loss_limit)
            mock_export.assert_called_once_with(self.report_id, self.loss_limit)
            self.assertEqual(res, expected_dict)

    def test_export_report_attribute_error(self):
        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            res = self.engine.export_report(self.report_id, self.loss_limit)
            self.assertEqual(res["report_id"], self.report_id)
            self.assertEqual(res["loss_limit"], self.loss_limit)

    def test_consume_stream_success(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=stream_data) as mock_stream:
            res = self.engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res, stream_data)

    def test_consume_stream_attribute_error(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            res = self.engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_standalone(self):
        portfolio_value = round(random.uniform(10000.0, 500000.0), 2)
        scenario_params = {
            "volatility": round(random.uniform(0.1, 0.5), 2),
            "drift": round(random.uniform(-0.02, 0.02), 2),
            "horizon_days": random.randint(1, 10)
        }
        iterations = random.randint(20, 100)

        result = run_monte_carlo_stress_test(
            self.portfolio_id,
            portfolio_value,
            scenario_params,
            iterations
        )

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["initial_value"], portfolio_value)
        self.assertEqual(result["iterations"], iterations)
        self.assertIn("simulation_id", result)
        self.assertIn("var_95", result)
        self.assertIn("expected_shortfall", result)


if __name__ == "__main__":
    unittest.main()