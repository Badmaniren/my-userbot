import unittest
from unittest.mock import patch
import random
import uuid
import math

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)
from skills import (
    db_storage,
    market_anomaly_detector,
    market_portfolio_data_exporter,
    market_portfolio_api_gateway
)


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.engine = MonteCarloStressEngine()
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.5), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(5, 30)

    def test_run_simulation_success(self):
        portfolio_data = {
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

        # Безопасное добавление атрибута в модуль для теста, если он отсутствует
        if not hasattr(db_storage, "fetch_portfolio"):
            setattr(db_storage, "fetch_portfolio", lambda pid: portfolio_data)

        if not hasattr(market_anomaly_detector, "get_current_anomaly_multiplier"):
            setattr(market_anomaly_detector, "get_current_anomaly_multiplier", lambda: 1.0)

        with patch.object(db_storage, 'fetch_portfolio', return_value=portfolio_data) as mock_fetch, \
             patch.object(market_anomaly_detector, 'get_current_anomaly_multiplier', return_value=1.0) as mock_anomaly:

            result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

            mock_fetch.assert_called_once_with(self.portfolio_id)
            mock_anomaly.assert_called_once()

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations)

    def test_run_simulation_default_portfolio_values(self):
        if hasattr(db_storage, "fetch_portfolio"):
            delattr(db_storage, "fetch_portfolio")

        if not hasattr(market_anomaly_detector, "get_current_anomaly_multiplier"):
            setattr(market_anomaly_detector, "get_current_anomaly_multiplier", lambda: 1.0)

        with patch.object(market_anomaly_detector, 'get_current_anomaly_multiplier', return_value=1.0) as mock_anomaly:
            result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

            mock_anomaly.assert_called_once()
            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(len(result["simulation_results"]), self.simulations)

    def test_export_report(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(1000.0, 10000.0), 2)
        expected_export_result = {"status": f"exported_{uuid.uuid4().hex[:4]}", "report_id": report_id}

        if not hasattr(market_portfolio_data_exporter, "export"):
            setattr(market_portfolio_data_exporter, "export", lambda r_id, l_lim: expected_export_result)

        with patch.object(market_portfolio_data_exporter, 'export', return_value=expected_export_result) as mock_export:
            res = self.engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res, expected_export_result)

    def test_consume_stream(self):
        random_payload = {"stream_id": uuid.uuid4().hex, "data": random.randint(1, 100)}

        if not hasattr(market_portfolio_api_gateway, "stream_payload"):
            setattr(market_portfolio_api_gateway, "stream_payload", lambda: random_payload)

        with patch.object(market_portfolio_api_gateway, 'stream_payload', return_value=random_payload) as mock_stream:
            res = self.engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res, random_payload)

    def test_run_monte_carlo_stress_test_functional(self):
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": self.horizon_days
        }
        iterations = random.randint(10, 30)

        res = run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(res, dict)
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["initial_value"], self.initial_value)
        self.assertEqual(res["iterations"], iterations)
        self.assertIn("simulation_id", res)
        self.assertIn("var_95", res)
        self.assertIn("expected_shortfall", res)
        self.assertIsInstance(res["var_95"], float)
        self.assertIsInstance(res["expected_shortfall"], float)


if __name__ == '__main__':
    unittest.main()