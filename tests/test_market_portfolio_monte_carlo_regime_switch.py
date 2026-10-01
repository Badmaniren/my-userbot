import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string

from skills.market_portfolio_monte_carlo_regime_switch import (
    RegimeSwitchSimulator,
    MarketPortfolioMonteCarloRegimeSwitch,
    market_portfolio_monte_carlo_regime_switch
)

class TestMarketPortfolioMonteCarloRegimeSwitch(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.bull_params = (random.uniform(0.05, 0.20), random.uniform(0.10, 0.20))
        self.bear_params = (random.uniform(-0.30, -0.10), random.uniform(0.25, 0.40))
        self.flat_params = (random.uniform(-0.02, 0.02), random.uniform(0.05, 0.12))
        self.transition_matrix = [
            [0.7, 0.2, 0.1],
            [0.3, 0.5, 0.2],
            [0.2, 0.3, 0.5]
        ]
        self.simulator = RegimeSwitchSimulator(
            self.bull_params, self.bear_params, self.flat_params, self.transition_matrix
        )
        self.model = MarketPortfolioMonteCarloRegimeSwitch(self.portfolio_id, self.simulator)

    def test_regime_switch_simulator_path(self):
        steps = random.randint(10, 50)
        seed = random.randint(1, 1000)
        path = self.simulator.generate_regime_path(steps, seed=seed)
        self.assertIsInstance(path, list)
        self.assertEqual(len(path), steps)
        for state in path:
            self.assertIn(state, [0, 1, 2])

    def test_monte_carlo_invalid_weights(self):
        initial_prices = [random.uniform(10, 100), random.uniform(10, 100)]
        invalid_weights = [random.uniform(0.1, 0.4), random.uniform(0.1, 0.4)]
        with self.assertRaises(ValueError):
            self.model.run_simulation(initial_prices, invalid_weights, num_simulations=10, time_horizon=5)

    @patch('skills.market_portfolio_monte_carlo_regime_switch.db_storage')
    def test_run_simulation_success(self, mock_db_storage):
        mock_db_storage.save_simulation_results.return_value = {"status": "saved"}
        initial_prices = [random.uniform(50, 150), random.uniform(50, 150)]
        weights = [0.5, 0.5]
        num_simulations = random.randint(20, 50)
        time_horizon = random.randint(10, 30)

        result = self.model.run_simulation(initial_prices, weights, num_simulations, time_horizon)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['portfolio_id'], self.portfolio_id)
        self.assertIn('final_values', result)
        self.assertIn('var_95', result)
        self.assertIn('cvar_95', result)
        self.assertEqual(len(result['final_values']), num_simulations)
        mock_db_storage.save_simulation_results.assert_called_once()

    def test_apply_stress_shock(self):
        initial_prices = [random.uniform(100, 200)]
        weights = [1.0]
        shock_magnitude = -random.uniform(0.1, 0.5)
        forced_regime = random.choice([0, 1, 2])
        steps = random.randint(5, 20)

        res = self.model.apply_stress_shock(initial_prices, weights, shock_magnitude, forced_regime, steps)
        self.assertIsInstance(res, dict)
        self.assertIn('stressed_mean_return', res)
        self.assertIn('max_drawdown', res)
        self.assertGreaterEqual(res['max_drawdown'], 0.0)

    @patch('skills.market_portfolio_monte_carlo_regime_switch.market_portfolio_data_exporter')
    def test_export_report(self, mock_exporter):
        random_export_data = {"data": uuid.uuid4().hex}
        mock_exporter.export_stream.return_value = random_export_data

        res = self.model.export_report()
        self.assertEqual(res, random_export_data)
        mock_exporter.export_stream.assert_called_once()

    @patch('skills.market_portfolio_monte_carlo_regime_switch.market_anomaly_detector')
    def test_check_market_anomalies(self, mock_detector):
        score = random.uniform(0.0, 1.0)
        mock_detector.analyze_portfolio_volatility.return_value = {'anomaly_score': score}
        initial_prices = [random.uniform(10, 50), random.uniform(10, 50)]

        res = self.model.check_market_anomalies(initial_prices)
        self.assertEqual(res, score)
        mock_detector.analyze_portfolio_volatility.assert_called_once_with(initial_prices)

    @patch('skills.market_portfolio_monte_carlo_regime_switch.market_portfolio_telegram_notifier')
    def test_trigger_tail_risk_alert(self, mock_notifier):
        chat_id = uuid.uuid4().hex
        var_value = -random.uniform(0.05, 0.20)
        self.model.trigger_tail_risk_alert(chat_id, var_value)
        mock_notifier.send_alert.assert_called_once()
        args, _ = mock_notifier.send_alert.call_args
        self.assertIn(chat_id, args[0])
        self.assertIn(str(var_value), args[0])

    @patch('skills.market_portfolio_monte_carlo_regime_switch.market_portfolio_stress_scenario_pipeline')
    def test_load_external_scenario(self, mock_pipeline):
        scenario_id = uuid.uuid4().hex
        expected_scenario = {"scenario_id": scenario_id, "impact": -0.15}
        mock_pipeline.fetch_scenario.return_value = expected_scenario

        res = self.model.load_external_scenario(scenario_id)
        self.assertEqual(res, expected_scenario)
        mock_pipeline.fetch_scenario.assert_called_once_with(scenario_id)

    @patch('skills.market_portfolio_monte_carlo_regime_switch.market_portfolio_audit_log_exporter')
    def test_audit_simulation_run(self, mock_audit):
        log_msg = uuid.uuid4().hex
        mock_audit.log_event.return_value = log_msg

        res = self.model.audit_simulation_run()
        self.assertEqual(res, log_msg)
        mock_audit.log_event.assert_called_once()

    @patch('skills.market_portfolio_monte_carlo_regime_switch.market_portfolio_valuation')
    def test_get_valuation(self, mock_valuation):
        val = random.uniform(1000.0, 50000.0)
        mock_valuation.get_current_portfolio_value.return_value = val

        res = self.model.get_valuation()
        self.assertEqual(res, val)
        mock_valuation.get_current_portfolio_value.assert_called_once_with(self.portfolio_id)


class TestMarketPortfolioMonteCarloRegimeSwitchIntegration(unittest.TestCase):

    def test_market_portfolio_monte_carlo_regime_switch_wrapper(self):
        portfolio_id = uuid.uuid4().hex
        runs = random.randint(50, 200)
        initial_capital = random.uniform(5000.0, 50000.0)
        config = {
            "portfolio_id": portfolio_id,
            "runs": runs,
            "initial_capital": initial_capital
        }

        res = market_portfolio_monte_carlo_regime_switch(config)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["portfolio_id"], portfolio_id)
        self.assertIn("var_95", res)
        self.assertIn("expected_tail_loss", res)
        self.assertIn("regime_probabilities", res)
        self.assertIsInstance(res["regime_probabilities"], dict)