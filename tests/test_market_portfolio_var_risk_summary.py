import unittest
from unittest.mock import patch, mock_open
import os
import uuid
import random
import json
from skills.market_portfolio_var_risk_summary import MarketPortfolioVaRRiskSummary, summarize_portfolio_var_risk

class TestMarketPortfolioVaRRiskSummary(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.var_metric = round(random.uniform(100.0, 50000.0), 2)
        self.risk_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.confidence = round(random.uniform(0.90, 0.99), 4)
        self.monte_carlo_metrics = {
            "var_estimate": round(random.uniform(500.0, 100000.0), 2),
            "iterations": random.randint(1000, 10000)
        }

    def test_market_portfolio_var_risk_summary_initialization(self):
        summary_obj = MarketPortfolioVaRRiskSummary(self.portfolio_id, self.var_metric, self.risk_level)
        self.assertEqual(summary_obj.portfolio_id, self.portfolio_id)
        self.assertEqual(summary_obj.var_metric, self.var_metric)
        self.assertEqual(summary_obj.risk_level, self.risk_level)

    def test_market_portfolio_var_risk_summary_generate_summary(self):
        summary_obj = MarketPortfolioVaRRiskSummary(self.portfolio_id, self.var_metric, self.risk_level)
        result = summary_obj.generate_summary()
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["var_metric"], self.var_metric)
        self.assertEqual(result["risk_level"], self.risk_level)
        self.assertEqual(result["status"], "aggregated")

    def test_market_portfolio_var_risk_summary_invalid_id(self):
        summary_obj = MarketPortfolioVaRRiskSummary("", self.var_metric, self.risk_level)
        with self.assertRaises(ValueError) as ctx:
            summary_obj.generate_summary()
        self.assertEqual(str(ctx.exception), "Invalid portfolio ID")

    def test_summarize_portfolio_var_risk_execution(self):
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            result = summarize_portfolio_var_risk(self.portfolio_id, self.confidence, self.monte_carlo_metrics)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["confidence_level"], self.confidence)
        self.assertEqual(result["total_var"], float(self.monte_carlo_metrics["var_estimate"]))
        self.assertEqual(result["status"], "aggregated")

        expected_filename = f"var_summary_{self.portfolio_id}.json"
        mock_file.assert_called_once_with(expected_filename, "w", encoding="utf-8")

if __name__ == "__main__":
    unittest.main()