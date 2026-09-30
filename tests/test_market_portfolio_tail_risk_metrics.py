import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
from skills.market_portfolio_tail_risk_metrics import MarketPortfolioTailRiskMetricsEvaluator

class TestMarketPortfolioTailRiskMetricsEvaluator(unittest.TestCase):

    def setUp(self):
        self.evaluator = MarketPortfolioTailRiskMetricsEvaluator()
        self.portfolio_id = uuid.uuid4().hex
        self.simulations_count = random.randint(100, 1000)
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)

    def test_calculate_expected_shortfall_random_data(self):
        random_returns = [random.uniform(-0.15, 0.10) for _ in range(self.simulations_count)]

        with patch('skills.market_portfolio_tail_risk_metrics.MarketPortfolioTailRiskMetricsEvaluator._fetch_simulation_data') as mock_fetch:
            mock_fetch.return_value = random_returns

            es_value = self.evaluator.calculate_expected_shortfall(self.portfolio_id, self.confidence_level)

            self.assertIsInstance(es_value, float)
            self.assertLessEqual(es_value, 0.0, "Expected Shortfall for losses should typically be non-positive or properly bounded.")

    def test_calculate_conditional_var_with_stream_mock(self):
        random_bytes_content = "".join(random.choices(string.ascii_letters + string.digits, k=128)).encode('utf-8')
        mock_stream = io.BytesIO(random_bytes_content)

        with patch('skills.market_portfolio_tail_risk_metrics.MarketPortfolioTailRiskMetricsEvaluator._open_data_stream') as mock_open:
            mock_open.return_value = mock_stream

            result = self.evaluator.calculate_conditional_var_from_stream(self.portfolio_id, self.confidence_level)

            self.assertIsNotNone(result)
            self.assertIn("cvar", result)
            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)

    def test_tail_risk_edge_cases(self):
        empty_returns = []

        with patch('skills.market_portfolio_tail_risk_metrics.MarketPortfolioTailRiskMetricsEvaluator._fetch_simulation_data') as mock_fetch:
            mock_fetch.return_value = empty_returns

            with self.assertRaises(ValueError):
                self.evaluator.calculate_expected_shortfall(self.portfolio_id, self.confidence_level)

    def test_metrics_integration_with_random_inputs(self):
        threshold_limit = random.uniform(0.01, 0.05)
        raw_payload = {
            "id": self.portfolio_id,
            "threshold": threshold_limit,
            "alpha": self.confidence_level,
            "payload_tag": uuid.uuid4().hex
        }

        mock_gateway = MagicMock()
        mock_gateway.get_metrics.return_value = raw_payload

        with patch('skills.market_portfolio_tail_risk_metrics.market_portfolio_api_gateway', mock_gateway):
            metrics = self.evaluator.evaluate_portfolio_tail_risk(self.portfolio_id)

            self.assertEqual(metrics["portfolio_id"], self.portfolio_id)
            self.assertEqual(metrics["alpha"], self.confidence_level)
            self.assertIn("risk_score", metrics)

if __name__ == '__main__':
    unittest.main()