import unittest
from unittest.mock import patch
import uuid
import random

from skills.market_portfolio_tail_risk_metrics_calculator import (
    MarketPortfolioTailRiskMetricsCalculator,
    calculate_tail_risk_metrics
)


class TestMarketPortfolioTailRiskMetricsCalculator(unittest.TestCase):

    def setUp(self):
        self.calculator = MarketPortfolioTailRiskMetricsCalculator()
        self.portfolio_id = uuid.uuid4().hex
        self.returns = [random.uniform(-0.1, 0.1) for _ in range(50)]
        self.confidence = random.choice([0.90, 0.95, 0.99])

    @patch('skills.market_portfolio_tail_risk_metrics_calculator.market_portfolio_var_liquidity_core')
    def test_calculate_tail_risks(self, mock_var_core):
        expected_var = random.uniform(0.01, 0.05)
        expected_es = random.uniform(0.02, 0.08)
        mock_var_core.compute_var.return_value = expected_var
        mock_var_core.compute_es.return_value = expected_es

        result = self.calculator.calculate_tail_risks(self.portfolio_id, self.returns, self.confidence)

        mock_var_core.compute_var.assert_called_once_with(self.returns, self.confidence)
        mock_var_core.compute_es.assert_called_once_with(self.returns, self.confidence)
        self.assertEqual(result["var"], expected_var)
        self.assertEqual(result["expected_shortfall"], expected_es)

    @patch('skills.market_portfolio_tail_risk_metrics_calculator.db_storage')
    def test_compute_tail_ratio(self, mock_db_storage):
        mock_db_storage.fetch_portfolio_history.return_value = None

        tail_ratio = self.calculator.compute_tail_ratio(self.portfolio_id, self.returns)

        mock_db_storage.fetch_portfolio_history.assert_called_once_with(self.portfolio_id)
        self.assertIsInstance(tail_ratio, float)
        self.assertGreaterEqual(tail_ratio, 0.0)

    @patch('skills.market_portfolio_tail_risk_metrics_calculator.db_storage')
    def test_compute_tail_ratio_empty_returns(self, mock_db_storage):
        mock_db_storage.fetch_portfolio_history.return_value = None

        tail_ratio = self.calculator.compute_tail_ratio(self.portfolio_id, [])

        self.assertEqual(tail_ratio, 0.0)

    @patch('skills.market_portfolio_tail_risk_metrics_calculator.db_storage')
    def test_compute_tail_ratio_zero_denominator(self, mock_db_storage):
        mock_db_storage.fetch_portfolio_history.return_value = None
        zero_p5_returns = [0.0] * 20

        tail_ratio = self.calculator.compute_tail_ratio(self.portfolio_id, zero_p5_returns)

        self.assertIsInstance(tail_ratio, float)

    @patch('skills.market_portfolio_tail_risk_metrics_calculator.market_parser')
    def test_evaluate_stream_risk(self, mock_market_parser):
        stream_obj = object()
        parsed_returns = [random.uniform(-0.05, 0.05) for _ in range(30)]
        mock_market_parser.parse_stream.return_value = parsed_returns

        with patch('skills.market_portfolio_tail_risk_metrics_calculator.db_storage') as mock_db:
            mock_db.fetch_portfolio_history.return_value = None
            result = self.calculator.evaluate_stream_risk(stream_obj)

        mock_market_parser.parse_stream.assert_called_once_with(stream_obj)
        self.assertIn("tail_ratio", result)
        self.assertIsInstance(result["tail_ratio"], float)

    @patch('skills.market_portfolio_tail_risk_metrics_calculator.market_portfolio_stress_monte_carlo_engine')
    def test_simulate_extreme_tail_events(self, mock_monte_carlo):
        simulations_count = random.randint(100, 1000)
        expected_sim_result = {uuid.uuid4().hex: random.uniform(1.0, 100.0)}
        mock_monte_carlo.run_simulation.return_value = expected_sim_result

        result = self.calculator.simulate_extreme_tail_events(self.portfolio_id, simulations_count)

        mock_monte_carlo.run_simulation.assert_called_once_with(self.portfolio_id, simulations_count)
        self.assertEqual(result, expected_sim_result)

    @patch('skills.market_portfolio_tail_risk_metrics_calculator.market_anomaly_detector')
    def test_check_tail_anomalies(self, mock_anomaly_detector):
        expected_anomaly_report = {uuid.uuid4().hex: random.choice([True, False])}
        mock_anomaly_detector.analyze_tail.return_value = expected_anomaly_report

        result = self.calculator.check_tail_anomalies(self.portfolio_id, self.returns)

        mock_anomaly_detector.analyze_tail.assert_called_once_with(self.portfolio_id, self.returns)
        self.assertEqual(result, expected_anomaly_report)

    @patch('skills.market_portfolio_tail_risk_metrics_calculator.db_storage')
    @patch('skills.market_portfolio_tail_risk_metrics_calculator.market_portfolio_var_liquidity_core')
    def test_calculate_tail_risk_metrics_helper(self, mock_var_core, mock_db_storage):
        mock_db_storage.fetch_portfolio_history.return_value = None
        expected_var = random.uniform(0.01, 0.05)
        expected_es = random.uniform(0.02, 0.08)
        mock_var_core.compute_var.return_value = expected_var
        mock_var_core.compute_es.return_value = expected_es

        result = calculate_tail_risk_metrics(self.portfolio_id, self.returns, self.confidence)

        self.assertIn("var", result)
        self.assertIn("expected_shortfall", result)
        self.assertIn("tail_ratio", result)
        self.assertEqual(result["var"], expected_var)
        self.assertEqual(result["expected_shortfall"], expected_es)
        self.assertIsInstance(result["tail_ratio"], float)


if __name__ == '__main__':
    unittest.main()