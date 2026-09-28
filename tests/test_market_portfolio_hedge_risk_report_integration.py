import unittest
import os
import uuid
import random
import json
from skills.market_portfolio_hedge_risk_report import generate_hedge_risk_report

class TestIntegrationMarketPortfolioHedgeRiskReport(unittest.TestCase):
    def setUp(self):
        self.output_file = f"test_report_{uuid.uuid4()}.json"

    def tearDown(self):
        if os.path.exists(self.output_file):
            try:
                os.remove(self.output_file)
            except OSError:
                pass

    def test_generate_hedge_risk_report_integration_flow(self):
        random_portfolio_id = str(uuid.uuid4())
        random_investor_id = str(uuid.uuid4())
        random_hedge_cost = round(random.uniform(1000.0, 50000.0), 2)

        valuation_metrics = {
            "total_value": round(random.uniform(100000.0, 5000000.0), 2),
            "var_95": round(random.uniform(5000.0, 50000.0), 2)
        }
        stress_metrics = {
            "scenario": "black_swan",
            "max_drawdown": round(random.uniform(0.1, 0.5), 4)
        }

        result = generate_hedge_risk_report(
            portfolio_id=random_portfolio_id,
            investor_id=random_investor_id,
            valuation_metrics=valuation_metrics,
            stress_metrics=stress_metrics,
            output_path=self.output_file
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], random_portfolio_id)
        self.assertEqual(result["investor_id"], random_investor_id)
        self.assertEqual(result["valuation_metrics"], valuation_metrics)
        self.assertEqual(result["stress_metrics"], stress_metrics)
        self.assertIn("report_id", result)

        self.assertTrue(os.path.exists(self.output_file), "Файл отчета не был создан на диске")

        with open(self.output_file, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data["report_id"], result["report_id"])
        self.assertEqual(file_data["portfolio_id"], random_portfolio_id)
        self.assertEqual(file_data["investor_id"], random_investor_id)
        self.assertEqual(file_data["valuation_metrics"], valuation_metrics)
        self.assertEqual(file_data["stress_metrics"], stress_metrics)

if __name__ == "__main__":
    unittest.main()