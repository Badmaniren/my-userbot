import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../skills")))

import unittest
import json
from market_portfolio_tax_calculator import market_portfolio_tax_calculator
from market_portfolio_stress_reporter import market_portfolio_stress_reporter

class TestAdvancedPortfolioRiskAndMetricsEpic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_data_path = "portfolio_risk_test_data.json"
        portfolio_payload = {
            "portfolio_id": "PRD-RISK-001",
            "assets": [
                {"ticker": "AAPL", "weight": 0.40, "current_price": 180.50, "historical_returns": [-0.012, 0.015, -0.008, 0.021, -0.035, 0.009, 0.014, -0.019, 0.005, 0.022]},
                {"ticker": "MSFT", "weight": 0.35, "current_price": 415.20, "historical_returns": [-0.009, 0.011, -0.005, 0.018, -0.028, 0.007, 0.012, -0.015, 0.003, 0.019]},
                {"ticker": "GOOGL", "weight": 0.25, "current_price": 142.80, "historical_returns": [-0.015, 0.019, -0.011, 0.025, -0.042, 0.011, 0.018, -0.023, 0.008, 0.026]}
            ],
            "confidence_level": 0.95,
            "tax_rate": 0.15,
            "realized_gains": 12500.0
        }
        with open(cls.test_data_path, "w", encoding="utf-8") as f:
            json.dump(portfolio_payload, f, indent=2)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_data_path):
            os.remove(cls.test_data_path)

    def test_var_cvar_and_tax_calculation(self):
        print("\n=== [PRACTICAL CHECK] Testing market_portfolio_tax_calculator ===")
        with open(self.test_data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        calc_result = market_portfolio_tax_calculator(raw_data)
        print(f"Tax & Risk Calculator Output -> {json.dumps(calc_result, indent=2)}")

        self.assertIsInstance(calc_result, dict)
        self.assertIn("var", calc_result)
        self.assertIn("cvar", calc_result)
        self.assertIn("tax_liability", calc_result)
        self.assertGreaterEqual(calc_result["var"], 0.0)
        self.assertGreaterEqual(calc_result["cvar"], 0.0)

    def test_stress_reporter_consolidation(self):
        print("\n=== [PRACTICAL CHECK] Testing market_portfolio_stress_reporter ===")
        with open(self.test_data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        risk_metrics = market_portfolio_tax_calculator(raw_data)
        report_payload = {
            "portfolio_id": raw_data["portfolio_id"],
            "risk_metrics": risk_metrics,
            "stress_scenarios": [
                {"scenario_name": "Market Crash -20%", "impact_multiplier": -0.20},
                {"scenario_name": "Interest Rate Hike", "impact_multiplier": -0.08}
            ]
        }

        report_result = market_portfolio_stress_reporter(report_payload)
        print(f"Stress Reporter Consolidated Output -> {json.dumps(report_result, indent=2)}")

        self.assertIsInstance(report_result, dict)
        self.assertIn("status", report_result)
        self.assertEqual(report_result["status"], "success")
        self.assertIn("report_summary", report_result)

if __name__ == "__main__":
    unittest.main()
