import unittest
import uuid
import random
from skills.market_portfolio_tail_risk_metrics_calculator import (
    MarketPortfolioTailRiskMetricsCalculator,
    calculate_tail_risk_metrics
)


class TestMarketPortfolioTailRiskMetricsCalculatorIntegration(unittest.TestCase):
    def setUp(self):
        self.calculator = MarketPortfolioTailRiskMetricsCalculator()
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.returns = [random.gauss(0.001, 0.02) for _ in range(100)]
        self.confidence = round(random.uniform(0.90, 0.99), 2)

    def test_calculate_tail_risks_integration(self):
        result = self.calculator.calculate_tail_risks(
            self.portfolio_id,
            self.returns,
            confidence=self.confidence
        )

        self.assertIsInstance(result, dict)
        self.assertIn("var", result)
        self.assertIn("expected_shortfall", result)
        self.assertIsInstance(result["var"], float)
        self.assertIsInstance(result["expected_shortfall"], float)

    def test_compute_tail_ratio_integration(self):
        tail_ratio = self.calculator.compute_tail_ratio(self.portfolio_id, self.returns)
        self.assertIsInstance(tail_ratio, float)
        self.assertGreaterEqual(tail_ratio, 0.0)

    def test_calculate_tail_risk_metrics_wrapper_integration(self):
        metrics = calculate_tail_risk_metrics(
            self.portfolio_id,
            self.returns,
            confidence_level=self.confidence
        )

        self.assertIsInstance(metrics, dict)
        self.assertIn("var", metrics)
        self.assertIn("expected_shortfall", metrics)
        self.assertIn("tail_ratio", metrics)
        self.assertIsInstance(metrics["var"], float)
        self.assertIsInstance(metrics["expected_shortfall"], float)
        self.assertIsInstance(metrics["tail_ratio"], float)

    def test_simulate_extreme_tail_events_integration(self):
        simulations_count = random.randint(10, 100)
        sim_result = self.calculator.simulate_extreme_tail_events(self.portfolio_id, simulations_count)
        self.assertIsInstance(sim_result, dict)

    def test_check_tail_anomalies_integration(self):
        anomaly_result = self.calculator.check_tail_anomalies(self.portfolio_id, self.returns)
        self.assertIsInstance(anomaly_result, dict)


if __name__ == "__main__":
    unittest.main()