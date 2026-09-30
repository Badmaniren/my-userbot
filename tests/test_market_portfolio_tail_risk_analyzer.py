import os
import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
from skills.market_portfolio_tail_risk_analyzer import MarketPortfolioTailRiskAnalyzer

class TestMarketPortfolioTailRiskAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = MarketPortfolioTailRiskAnalyzer()
        self.random_portfolio_id = uuid.uuid4().hex
        self.random_confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.random_simulations_count = random.randint(1000, 50000)

    def test_calculate_expected_shortfall_success(self):
        mock_returns = [random.uniform(-0.15, -0.01) for _ in range(100)]
        returns_sorted = sorted(mock_returns)
        index = max(1, int((1 - self.random_confidence_level) * len(returns_sorted)))
        if index > len(returns_sorted):
            index = len(returns_sorted)
        tail_returns = returns_sorted[:index]
        expected_es = sum(tail_returns) / len(tail_returns)

        with patch('skills.market_portfolio_tail_risk_analyzer.market_portfolio_stress_monte_carlo_engine') as mock_engine:
            mock_engine.fetch_simulation_results.return_value = {
                'portfolio_id': self.random_portfolio_id,
                'returns': mock_returns
            }

            result = self.analyzer.calculate_expected_shortfall(
                self.random_portfolio_id,
                self.random_confidence_level
            )

            self.assertIsInstance(result, dict)
            self.assertIn('expected_shortfall', result)
            self.assertEqual(result['portfolio_id'], self.random_portfolio_id)
            self.assertAlmostEqual(result['expected_shortfall'], expected_es, places=4)

    def test_calculate_cvar_empty_data_handling(self):
        random_error_code = ''.join(random.choices(string.ascii_uppercase, k=6))

        with patch('skills.market_portfolio_tail_risk_analyzer.market_portfolio_stress_monte_carlo_engine') as mock_engine:
            mock_engine.fetch_simulation_results.return_value = {
                'portfolio_id': self.random_portfolio_id,
                'returns': []
            }

            with self.assertRaises(ValueError) as ctx:
                self.analyzer.calculate_cvar(
                    self.random_portfolio_id,
                    self.random_confidence_level
                )

            self.assertTrue(len(str(ctx.exception)) > 0)

    def test_analyze_tail_risk_with_io_stream(self):
        random_bytes_content = uuid.uuid4().bytes + os.urandom(32)
        mock_stream = io.BytesIO(random_bytes_content)

        with patch('skills.market_portfolio_tail_risk_analyzer.db_storage') as mock_db:
            mock_db.load_binary_stream.return_value = mock_stream

            risk_report = self.analyzer.analyze_from_storage(
                self.random_portfolio_id,
                self.random_simulations_count
            )

            self.assertIsInstance(risk_report, dict)
            self.assertEqual(risk_report.get('target_portfolio'), self.random_portfolio_id)
            self.assertIn('tail_risk_metric', risk_report)

    def test_stress_monte_carlo_integration_trigger(self):
        random_anomaly_flag = random.choice([True, False])
        random_threshold = random.uniform(0.01, 0.05)

        with patch('skills.market_portfolio_tail_risk_analyzer.market_anomaly_detector') as mock_detector, \
             patch('skills.market_portfolio_tail_risk_analyzer.market_portfolio_alert_dispatcher') as mock_dispatcher:

            mock_detector.check_tail_risk_anomaly.return_value = {
                'is_anomaly': random_anomaly_flag,
                'threshold': random_threshold
            }

            dispatch_id = uuid.uuid4().hex
            mock_dispatcher.dispatch_alert.return_value = {'dispatch_id': dispatch_id}

            response = self.analyzer.evaluate_and_dispatch_tail_risk(
                self.random_portfolio_id,
                random_threshold
            )

            self.assertEqual(response['status'], 'processed')
            self.assertEqual(response['dispatch_confirmation'], dispatch_id)
            mock_detector.check_tail_risk_anomaly.assert_called_once()

    def test_pipeline_data_flow_integrity(self):
        random_seed_value = random.randint(1, 1000000)

        with patch('skills.market_portfolio_tail_risk_analyzer.market_portfolio_scenario_simulator') as mock_simulator:
            mock_simulator.run_monte_carlo.return_value = {
                'seed': random_seed_value,
                'outcomes': [random.gauss(-0.02, 0.05) for _ in range(500)]
            }

            metrics = self.analyzer.run_simulation_pipeline(
                self.random_portfolio_id,
                self.random_simulations_count
            )

            self.assertEqual(metrics['simulation_seed'], random_seed_value)
            self.assertIn('conditional_value_at_risk', metrics)
            self.assertGreaterEqual(metrics['conditional_value_at_risk'], -1.0)

if __name__ == '__main__':
    unittest.main()