import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_hedge_synthesizer import (
    MarketPortfolioHedgeSynthesizer,
    HedgeSynthesisError
)

class TestMarketPortfolioHedgeSynthesizer(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.backtester = MagicMock()
        self.scenario_simulator = MagicMock()

        self.synthesizer = MarketPortfolioHedgeSynthesizer(
            db_storage=self.db_storage,
            market_portfolio_backtester=self.backtester,
            market_portfolio_scenario_simulator=self.scenario_simulator
        )

    def test_synthesize_hedge_parameters_success(self):
        portfolio_id = uuid.uuid4().hex
        var_threshold = round(random.uniform(0.01, 0.15), 4)
        cvar_threshold = round(var_threshold * random.uniform(1.2, 2.0), 4)
        expected_strike = round(random.uniform(100.0, 5000.0), 2)
        expected_premium = round(random.uniform(5.0, 150.0), 2)

        mock_metrics = {
            "var": var_threshold,
            "cvar": cvar_threshold,
            "asset_id": portfolio_id
        }

        with patch.object(self.synthesizer, '_extract_tail_risk_metrics', return_value=mock_metrics) as mock_extract, \
             patch.object(self.synthesizer, '_calculate_optimal_strike', return_value=expected_strike) as mock_strike, \
             patch.object(self.synthesizer, '_price_protective_option', return_value=expected_premium) as mock_price:

            result = self.synthesizer.synthesize_hedge(portfolio_id)

            mock_extract.assert_called_once_with(portfolio_id)
            mock_strike.assert_called_once_with(mock_metrics)
            mock_price.assert_called_once_with(expected_strike, mock_metrics)

            self.assertIn("strike", result)
            self.assertIn("premium", result)
            self.assertEqual(result["strike"], expected_strike)
            self.assertEqual(result["premium"], expected_premium)
            self.assertEqual(result["portfolio_id"], portfolio_id)

    def test_synthesize_hedge_raises_error_on_invalid_data(self):
        portfolio_id = uuid.uuid4().hex

        with patch.object(self.synthesizer, '_extract_tail_risk_metrics', side_effect=Exception("Database connection failed")):
            with self.assertRaises(HedgeSynthesisError):
                self.synthesizer.synthesize_hedge(portfolio_id)

    def test_extract_tail_risk_metrics_parses_stream(self):
        portfolio_id = uuid.uuid4().hex
        random_bytes = ''.join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')
        mock_file_stream = io.BytesIO(random_bytes)

        self.db_storage.fetch_stream.return_value = mock_file_stream

        metrics = self.synthesizer._extract_tail_risk_metrics(portfolio_id)

        self.assertIsInstance(metrics, dict)
        self.db_storage.fetch_stream.assert_called_once_with(portfolio_id)

    def test_calculate_optimal_strike_logic(self):
        var_val = round(random.uniform(0.02, 0.08), 4)
        cvar_val = round(var_val * 1.5, 4)
        spot_price = round(random.uniform(50.0, 1000.0), 2)

        metrics = {
            "var": var_val,
            "cvar": cvar_val,
            "spot_price": spot_price
        }

        strike = self.synthesizer._calculate_optimal_strike(metrics)

        expected_strike = spot_price * (1.0 - var_val)
        self.assertAlmostEqual(strike, expected_strike, places=2)

    def test_price_protective_option_output(self):
        strike = round(random.uniform(200.0, 2000.0), 2)
        volatility = round(random.uniform(0.1, 0.9), 4)

        metrics = {
            "volatility": volatility,
            "time_to_expiry": random.choice([30, 60, 90, 180])
        }

        premium = self.synthesizer._price_protective_option(strike, metrics)

        self.assertIsInstance(premium, float)
        self.assertGreater(premium, 0.0)

    def test_integration_with_scenario_simulator(self):
        portfolio_id = uuid.uuid4().hex
        simulation_seed = ''.join(random.choices(string.ascii_lowercase, k=10))

        self.scenario_simulator.run_simulation.return_value = {
            "simulation_id": simulation_seed,
            "success": True,
            "projected_loss": round(random.uniform(1000.0, 50000.0), 2)
        }

        result = self.synthesizer.simulate_hedge_impact(portfolio_id, simulation_seed)

        self.assertTrue(result["success"])
        self.assertEqual(result["simulation_id"], simulation_seed)
        self.scenario_simulator.run_simulation.assert_called_once_with(portfolio_id, simulation_seed)

if __name__ == '__main__':
    unittest.main()