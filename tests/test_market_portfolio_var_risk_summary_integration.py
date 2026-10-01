import unittest
import os
import uuid
import random
from skills.market_portfolio_var_risk_summary import MarketPortfolioVaRRiskSummary, summarize_portfolio_var_risk


class TestMarketPortfolioVaRRiskSummaryIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.var_metric = round(random.uniform(1000.0, 50000.0), 2)
        self.risk_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.confidence = round(random.uniform(0.90, 0.99), 2)
        self.summary_file_path = f"var_summary_{self.portfolio_id}.json"

    def tearDown(self):
        if os.path.exists(self.summary_file_path):
            os.remove(self.summary_file_path)

    def test_market_portfolio_var_risk_summary_class(self):
        summary_instance = MarketPortfolioVaRRiskSummary(
            portfolio_id=self.portfolio_id,
            var_metric=self.var_metric,
            risk_level=self.risk_level
        )

        result = summary_instance.generate_summary()

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["var_metric"], self.var_metric)
        self.assertEqual(result["risk_level"], self.risk_level)
        self.assertEqual(result["status"], "aggregated")

    def test_summarize_portfolio_var_risk_integration(self):
        monte_carlo_metrics = {
            "var_estimate": self.var_metric,
            "simulation_runs": random.randint(1000, 10000)
        }

        result = summarize_portfolio_var_risk(
            portfolio_id=self.portfolio_id,
            confidence=self.confidence,
            monte_carlo_metrics=monte_carlo_metrics
        )

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["confidence_level"], self.confidence)
        self.assertEqual(result["total_var"], float(self.var_metric))
        self.assertEqual(result["status"], "aggregated")

        self.assertTrue(os.path.exists(self.summary_file_path), "Файл сводки рисков должен быть создан на диске")

    def test_invalid_portfolio_id_raises_value_error(self):
        summary_instance = MarketPortfolioVaRRiskSummary(
            portfolio_id="",
            var_metric=self.var_metric,
            risk_level=self.risk_level
        )
        with self.assertRaises(ValueError):
            summary_instance.generate_summary()


if __name__ == "__main__":
    unittest.main()