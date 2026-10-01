import unittest
import uuid
import random
from skills.market_portfolio_monte_carlo_regime_switch import (
    RegimeSwitchSimulator,
    MarketPortfolioMonteCarloRegimeSwitch,
    market_portfolio_monte_carlo_regime_switch
)

class TestMarketPortfolioMonteCarloRegimeSwitchIntegration(unittest.TestCase):
    def test_monte_carlo_regime_switch_integration_flow(self):
        portfolio_id = f"test_port_{uuid.uuid4()}"
        runs = random.randint(50, 200)
        initial_capital = round(random.uniform(5000.0, 50000.0), 2)

        config = {
            "portfolio_id": portfolio_id,
            "runs": runs,
            "initial_capital": initial_capital
        }

        result = market_portfolio_monte_carlo_regime_switch(config)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertIn("var_95", result)
        self.assertIn("expected_tail_loss", result)
        self.assertIn("regime_probabilities", result)
        self.assertLess(result["var_95"], 0)
        self.assertLess(result["expected_tail_loss"], 0)

        bull_params = (0.1, 0.15)
        bear_params = (-0.2, 0.3)
        flat_params = (0.02, 0.1)
        transition_matrix = [
            [0.7, 0.2, 0.1],
            [0.3, 0.6, 0.1],
            [0.2, 0.2, 0.6]
        ]

        simulator = RegimeSwitchSimulator(bull_params, bear_params, flat_params, transition_matrix)
        mc_engine = MarketPortfolioMonteCarloRegimeSwitch(portfolio_id, simulator)

        initial_prices = [100.0, 200.0]
        weights = [0.5, 0.5]

        simulation_res = mc_engine.run_simulation(initial_prices, weights, num_simulations=10, time_horizon=20)

        self.assertIsInstance(simulation_res, dict)
        self.assertEqual(simulation_res["portfolio_id"], portfolio_id)
        self.assertIn("final_values", simulation_res)
        self.assertIn("var_95", simulation_res)
        self.assertIn("cvar_95", simulation_res)
        self.assertEqual(len(simulation_res["final_values"]), 10)

if __name__ == "__main__":
    unittest.main()