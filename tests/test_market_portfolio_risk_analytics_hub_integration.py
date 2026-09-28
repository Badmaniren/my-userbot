import unittest
import uuid
import random
import os

from skills.market_portfolio_risk_analytics_hub import market_portfolio_risk_analytics_hub
from skills.db_storage import db_storage
from skills.market_portfolio_performance_analytics import market_portfolio_performance_analytics
from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter
from skills.market_report_generator import market_report_generator

class TestMarketPortfolioRiskAnalyticsHubIntegration(unittest.TestCase):
    def test_risk_analytics_hub_aggregation_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_capital = round(random.uniform(10000.0, 1000000.0), 2)
        stress_shock_pct = round(random.uniform(-50.0, -5.0), 2)

        test_data = {
            "portfolio_id": portfolio_id,
            "capital": initial_capital,
            "shock_pct": stress_shock_pnct := stress_shock_pct,
            "volatility_window": random.randint(30, 365)
        }

        db_storage.save_portfolio_state(portfolio_id, test_data)

        perf_metrics = market_portfolio_performance_analytics.calculate_metrics(portfolio_id)
        stress_report = market_portfolio_stress_reporter.run_stress_test(portfolio_id, stress_shock_pct)
        
        hub_result = market_portfolio_risk_analytics_hub.generate_comprehensive_risk_report(
            portfolio_id=portfolio_id,
            performance_data=perf_metrics,
            stress_data=stress_report
        )

        self.assertIsNotNone(hub_result)
        self.assertIn("risk_score", hub_result)
        self.assertEqual(hub_result["portfolio_id"], portfolio_id)

        report_filename = f"report_{portfolio_id}.json"
        market_report_generator.export_report(report_filename, hub_result)

        self.assertTrue(os.path.exists(report_filename))

        stored_record = db_storage.get_risk_report(portfolio_id)
        self.assertEqual(stored_record.get("portfolio_id"), portfolio_id)

        if os.path.exists(report_filename):
            os.remove(report_filename)

if __name__ == "__main__":
    unittest.main()