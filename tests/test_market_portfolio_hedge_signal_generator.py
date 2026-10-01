import unittest
from unittest.mock import patch
import uuid
import random

from skills.market_portfolio_hedge_signal_generator import (
    MarketPortfolioHedgeSignalGenerator,
    market_portfolio_hedge_signal_generator
)


class TestMarketPortfolioHedgeSignalGenerator(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.portfolio_value = random.uniform(100000.0, 5000000.0)
        self.var_value = self.portfolio_value * random.uniform(0.01, 0.1)
        self.liquidity_ratio = random.uniform(0.01, 1.0)
        self.stress_loss_pct = random.uniform(0.05, 0.5)

    def test_calculate_hedge_ratio_positive(self):
        generator = MarketPortfolioHedgeSignalGenerator()
        ratio = generator.calculate_hedge_ratio(
            self.portfolio_value,
            self.var_value,
            self.liquidity_ratio,
            self.stress_loss_pct
        )
        self.assertIsInstance(ratio, float)
        self.assertGreaterEqual(ratio, 0.0)
        self.assertLessEqual(ratio, 1.0)

    def test_calculate_hedge_ratio_invalid_portfolio_value(self):
        generator = MarketPortfolioHedgeSignalGenerator()
        invalid_vals = [0.0, -random.uniform(1.0, 1000.0)]
        for val in invalid_vals:
            with self.assertRaises(ValueError):
                generator.calculate_hedge_ratio(
                    val,
                    self.var_value,
                    self.liquidity_ratio,
                    self.stress_loss_pct
                )

    def test_select_protective_instruments_low_liquidity(self):
        generator = MarketPortfolioHedgeSignalGenerator()
        instruments = generator.select_protective_instruments(0.5, 0.05)
        self.assertEqual(instruments, ["CASH", "INVERSE_ETF"])

    def test_select_protective_instruments_medium_liquidity(self):
        generator = MarketPortfolioHedgeSignalGenerator()
        instruments = generator.select_protective_instruments(0.5, 0.2)
        self.assertEqual(instruments, ["INVERSE_ETF", "PUT_OPTIONS"])

    def test_select_protective_instruments_high_hedge_ratio(self):
        generator = MarketPortfolioHedgeSignalGenerator()
        instruments = generator.select_protective_instruments(0.8, 0.5)
        self.assertEqual(instruments, ["INDEX_FUTURES", "PUT_OPTIONS"])

    def test_select_protective_instruments_default(self):
        generator = MarketPortfolioHedgeSignalGenerator()
        instruments = generator.select_protective_instruments(0.3, 0.5)
        self.assertEqual(instruments, ["PUT_OPTIONS"])

    def test_generate_hedge_signal_with_mocks(self):
        mock_var_core = unittest.mock.MagicMock()
        mock_var_core.get_var_and_liquidity.return_value = {
            "portfolio_value": self.portfolio_value,
            "var_value": self.var_value,
            "liquidity_ratio": self.liquidity_ratio
        }

        mock_stress_engine = unittest.mock.MagicMock()
        mock_stress_engine.run_stress_test.return_value = {
            "stress_loss_pct": self.stress_loss_pct,
            "scenario_name": f"scenario_{uuid.uuid4().hex[:4]}"
        }

        mock_db = unittest.mock.MagicMock()

        generator = MarketPortfolioHedgeSignalGenerator(
            var_liquidity_core=mock_var_core,
            stress_engine=mock_stress_engine,
            db_storage=mock_db
        )

        signal = generator.generate_hedge_signal(self.portfolio_id)

        self.assertIn("signal_id", signal)
        self.assertEqual(signal["portfolio_id"], self.portfolio_id)
        self.assertIn("hedge_ratio", signal)
        self.assertIn("protective_instruments", signal)
        self.assertIn("instrument_type", signal)
        mock_db.save_signal.assert_called_once()

    def test_generate_hedge_signal_invalid_var_data(self):
        mock_var_core = unittest.mock.MagicMock()
        mock_var_core.get_var_and_liquidity.return_value = {
            "portfolio_value": 0.0,
            "var_value": self.var_value,
            "liquidity_ratio": self.liquidity_ratio
        }

        generator = MarketPortfolioHedgeSignalGenerator(var_liquidity_core=mock_var_core)
        with self.assertRaises(ValueError):
            generator.generate_hedge_signal(self.portfolio_id)


class TestMarketPortfolioHedgeSignalGeneratorIntegration(unittest.TestCase):

    def test_market_portfolio_hedge_signal_generator_function(self):
        portfolio_id = f"int_port_{uuid.uuid4().hex[:8]}"
        portfolio_value = random.uniform(50000.0, 1000000.0)
        var_value = portfolio_value * 0.05
        liquidity_ratio = 0.3
        stress_loss_pct = 0.2

        generator_input = {
            "portfolio_id": portfolio_id,
            "var_data": {
                "portfolio_value": portfolio_value,
                "var_value": var_value,
                "liquidity_ratio": liquidity_ratio
            },
            "stress_data": {
                "stress_loss_pct": stress_loss_pct
            }
        }

        with patch("skills.market_portfolio_hedge_signal_generator.db_storage") as mock_db_func:
            signal = market_portfolio_hedge_signal_generator(generator_input)

            self.assertIsInstance(signal, dict)
            self.assertEqual(signal["portfolio_id"], portfolio_id)
            self.assertIn("hedge_ratio", signal)
            self.assertIn("protective_instruments", signal)
            mock_db_func.assert_called_once()

    def test_market_portfolio_hedge_signal_generator_invalid_input(self):
        generator_input = {
            "portfolio_id": f"err_port_{uuid.uuid4().hex[:8]}",
            "var_data": {
                "portfolio_value": -100.0
            }
        }

        with patch("skills.market_portfolio_hedge_signal_generator.db_storage"):
            with self.assertRaises(ValueError):
                market_portfolio_hedge_signal_generator(generator_input)


if __name__ == "__main__":
    unittest.main()