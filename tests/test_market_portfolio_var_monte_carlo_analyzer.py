import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
from skills.market_portfolio_var_monte_carlo_analyzer import MarketPortfolioVaRMonteCarloAnalyzer

class TestMarketPortfolioVaRMonteCarloAnalyzer(unittest.TestCase):
    def setUp(self):
        self.db_mock = MagicMock()
        self.stress_engine_mock = MagicMock()
        self.scenario_simulator_mock = MagicMock()
        self.analyzer = MarketPortfolioVaRMonteCarloAnalyzer(
            db_storage=self.db_mock,
            market_portfolio_stress_monte_carlo_engine=self.stress_engine_mock,
            market_portfolio_scenario_simulator=self.scenario_simulator_mock
        )

    def test_calculate_var_monte_carlo_logic(self):
        portfolio_id = uuid.uuid4().hex
        initial_val = float(random.randint(10000, 500000))
        simulations = random.randint(100, 1000)
        confidence = 0.95

        with patch.object(MarketPortfolioVaRMonteCarloAnalyzer, '_fetch_historical_data', return_value={
            'portfolio_id': portfolio_id,
            'initial_value': initial_val,
            'returns_sample': [0.01, -0.02, 0.005, -0.01]
        }):
            result = self.analyzer.compute_var(portfolio_id, confidence, simulations, 1)

            self.assertEqual(result['portfolio_id'], portfolio_id)
            self.assertIn('var_value', result)
            self.assertGreaterEqual(result['var_value'], 0.0)
            self.assertEqual(result['simulation_stats']['simulations_run'], simulations)
            self.db_mock.save_var_analysis.assert_called_once()

    def test_edge_case_empty_returns(self):
        portfolio_id = uuid.uuid4().hex
        with patch.object(MarketPortfolioVaRMonteCarloAnalyzer, '_fetch_historical_data', return_value={
            'portfolio_id': portfolio_id,
            'returns_sample': []
        }):
            with self.assertRaises(ValueError):
                self.analyzer.compute_var(portfolio_id, 0.95, 100, 1)

    def test_integration_with_stress_engine(self):
        portfolio_id = uuid.uuid4().hex
        scenario = uuid.uuid4().hex
        shock = random.uniform(0.1, 0.5)

        self.stress_engine_mock.run_stress_monte_carlo.return_value = {
            'shock_applied': shock,
            'stressed_var': 5000.0
        }

        result = self.analyzer.compute_stressed_var(portfolio_id, scenario, 0.99, 500)

        self.assertEqual(result['scenario'], scenario)
        self.assertEqual(result['shock_applied'], shock)
        self.stress_engine_mock.run_stress_monte_carlo.assert_called_with(
            portfolio_id=portfolio_id,
            simulations=500,
            scenario_name=scenario
        )

    def test_anomaly_detection_trigger(self):
        portfolio_id = uuid.uuid4().hex
        var_val = float(random.randint(100, 1000))

        with patch('skills.market_portfolio_var_monte_carlo_analyzer.market_anomaly_detector') as mock_detector:
            mock_detector.evaluate_var_anomaly.return_value = True
            is_anomaly = self.analyzer.check_portfolio_var_anomaly(portfolio_id, var_val)

            self.assertTrue(is_anomaly)
            mock_detector.evaluate_var_anomaly.assert_called_with(portfolio_id, var_val)

    def test_export_data_stream_io(self):
        portfolio_id = uuid.uuid4().hex
        random_data = uuid.uuid4().hex.encode('utf-8')

        with patch('skills.market_portfolio_var_monte_carlo_analyzer.market_portfolio_data_exporter') as mock_exporter:
            mock_exporter.export_stream.return_value = random_data
            result = self.analyzer.export_analysis_report(portfolio_id)

            self.assertEqual(result, random_data)
            mock_exporter.export_stream.assert_called_with(portfolio_id)

if __name__ == '__main__':
    unittest.main()
