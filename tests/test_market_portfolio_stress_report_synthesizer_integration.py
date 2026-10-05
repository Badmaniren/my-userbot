import unittest
import uuid
import random

from skills.market_portfolio_stress_report_synthesizer import (
    market_portfolio_stress_report_synthesizer,
    MarketPortfolioStressReportSynthesizer
)
from skills.db_storage import db_storage

class TestMarketPortfolioStressReportSynthesizerIntegration(unittest.TestCase):
    def test_synthesizer_real_integration(self):
        rand_suffix = uuid.uuid4().hex[:8]
        portfolio_id = f"port_{rand_suffix}"
        report_id = f"rep_{rand_suffix}"

        payload = {
            "portfolio_id": portfolio_id,
            "report_id": report_id,
            "matrix_evaluation": {
                "status": "EVALUATED",
                "risk_score": random.uniform(1.0, 10.0)
            },
            "monte_carlo_simulation": {
                "iterations": random.randint(50, 500),
                "mean_outcome": random.uniform(-1000.0, 5000.0)
            }
        }

        result = market_portfolio_stress_report_synthesizer(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("report_id"), report_id)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("status"), "SYNTHESIZED")
        self.assertIn("entropy", result)
        self.assertIn("aggregated_metrics", result)

        metrics = result["aggregated_metrics"]
        self.assertEqual(metrics["matrix_status"], "EVALUATED")
        self.assertEqual(metrics["mc_simulations"], payload["monte_carlo_simulation"]["iterations"])
        self.assertEqual(metrics["mean_outcome"], payload["monte_carlo_simulation"]["mean_outcome"])

        class_instance = MarketPortfolioStressReportSynthesizer()
        class_result = class_instance.synthesize_report(portfolio_id, {"report_id": report_id})
        self.assertEqual(class_result.get("report_id"), report_id)
        self.assertEqual(class_result.get("portfolio_id"), portfolio_id)
        self.assertEqual(class_result.get("status"), "SYNTHESIZED")

    def test_synthesizer_invalid_payload_raises(self):
        with self.assertRaises(ValueError):
            market_portfolio_stress_report_synthesizer(None)

        with self.assertRaises(ValueError):
            market_portfolio_stress_report_synthesizer({})

        with self.assertRaises(ValueError):
            market_portfolio_stress_report_synthesizer({"portfolio_id": "p1"})

if __name__ == "__main__":
    unittest.main()