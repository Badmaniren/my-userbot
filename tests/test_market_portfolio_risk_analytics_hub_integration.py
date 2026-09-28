import unittest
import uuid
import random
from skills.market_portfolio_risk_analytics_hub import start_new, market_portfolio_risk_analytics_hub
from skills.db_storage import db_storage
from skills.market_portfolio_performance_analytics import market_portfolio_performance_analytics
from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter
from skills.market_report_generator import market_report_generator
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent

class TestMarketPortfolioRiskAnalyticsHubIntegration(unittest.TestCase):
    def test_comprehensive_risk_report_integration(self):
        rand_portfolio_id = f"port-{uuid.uuid4()}"
        rand_risk_score = round(random.uniform(0.01, 0.25), 4)
        rand_loss = round(random.uniform(1000.0, 50000.0), 2)

        performance_data = {
            "portfolio_id": rand_portfolio_id,
            "risk_score": rand_risk_score,
            "volatility": rand_risk_score * 1.2
        }

        stress_data = {
            "scenario": "CRASH_2008_SIM",
            "projected_loss": rand_loss
        }

        report = market_portfolio_risk_analytics_hub.generate_comprehensive_risk_report(
            portfolio_id=rand_portfolio_id,
            performance_data=performance_data,
            stress_data=stress_data
        )

        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("portfolio_id"), rand_portfolio_id)
        self.assertEqual(report.get("risk_score"), rand_risk_score)
        self.assertEqual(report.get("status"), "success")
        self.assertIn("performance_metrics", report)
        self.assertIn("stress_test_data", report)

    def test_start_new_integration_flow(self):
        rand_portfolio_id = f"port-{uuid.uuid4()}"
        rand_limit = round(random.uniform(0.05, 0.50), 2)

        db_storage.save_portfolio({
            "portfolio_id": rand_portfolio_id,
            "volatility_limit": rand_limit
        })

        dependencies = {
            "db_storage": db_storage,
            "market_portfolio_collector_agent": market_portfolio_collector_agent,
            "market_portfolio_stress_reporter": market_portfolio_stress_reporter
        }

        result = start_new(dependencies)

        self.assertIsInstance(result, dict)
        if "portfolio_id" in result:
            self.assertEqual(result.get("portfolio_id"), rand_portfolio_id)
            self.assertEqual(result.get("risk_score"), rand_limit)
            self.assertEqual(result.get("status"), "success")
        else:
            self.assertIn("aggregated", result)
            self.assertTrue(result.get("aggregated"))

if __name__ == "__main__":
    unittest.main()