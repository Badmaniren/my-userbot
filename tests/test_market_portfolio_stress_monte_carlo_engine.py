import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
from skills.market_portfolio_stress_monte_carlo_engine import MonteCarloStressEngine

class TestMonteCarloStressEngine(unittest.TestCase):
    def setUp(self):
        self.engine = MonteCarloStressEngine()

    def test_run_simulation_valid_data(self):
        rand_portfolio_id = str(uuid.uuid4())
        rand_simulations_count = random.randint(100, 1000)
        rand_horizon_days = random.randint(1, 30)
        rand_initial_value = random.uniform(10000.0, 1000000.0)
        rand_volatility = random.uniform(0.1, 0.9)
        rand_drift = random.uniform(-0.05, 0.05)

        mock_db = MagicMock()
        mock_db.fetch_portfolio.return_value = {
            "portfolio_id": rand_portfolio_id,
            "initial_value": rand_initial_value,
            "volatility": rand_volatility,
            "drift": rand_drift
        }

        with patch("skills.market_portfolio_stress_monte_carlo_engine.db_storage", mock_db):
            result = self.engine.run_simulation(
                portfolio_id=rand_portfolio_id,
                simulations=rand_simulations_count,
                horizon_days=rand_horizon_days
            )

        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], rand_portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertEqual(len(result["simulation_results"]), rand_simulations_count)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)

    def test_run_simulation_with_anomaly_detector(self):
        rand_portfolio_id = str(uuid.uuid4())
        rand_anomaly_factor = random.uniform(1.2, 3.0)

        mock_detector = MagicMock()
        mock_detector.get_current_anomaly_multiplier.return_value = rand_anomaly_factor

        with patch("skills.market_portfolio_stress_monte_carlo_engine.market_anomaly_detector", mock_detector):
            multiplier = self.engine._get_anomaly_adjustment()

        self.assertEqual(multiplier, rand_anomaly_factor)
        mock_detector.get_current_anomaly_multiplier.assert_called_once()

    def test_export_stress_report(self):
        rand_report_id = ''.join(random.choices(string.ascii_lowercase, k=10))
        rand_loss_limit = random.uniform(5000.0, 50000.0)

        mock_exporter = MagicMock()
        mock_exporter.export.return_value = {"status": "success", "report_id": rand_report_id}

        with patch("skills.market_portfolio_stress_monte_carlo_engine.market_portfolio_data_exporter", mock_exporter):
            output = self.engine.export_report(rand_report_id, rand_loss_limit)

        self.assertEqual(output["report_id"], rand_report_id)
        self.assertEqual(output["status"], "success")

    def test_stream_monte_carlo_payload(self):
        rand_bytes_count = random.randint(50, 500)
        random_payload = bytes(random.getrandbits(8) for _ in range(rand_bytes_count))
        mock_stream = io.BytesIO(random_payload)

        mock_gateway = MagicMock()
        mock_gateway.stream_payload.return_value = mock_stream

        with patch("skills.market_portfolio_stress_monte_carlo_engine.market_portfolio_api_gateway", mock_gateway):
            streamed_data = self.engine.consume_stream()

        self.assertEqual(streamed_data.read(), random_payload)

if __name__ == "__main__":
    unittest.main()