import unittest
import uuid
import random
from skills.market_portfolio_tail_risk_analyzer import market_portfolio_tail_risk_analyzer, MarketPortfolioTailRiskAnalyzer
from skills.db_storage import db_storage

class IntegrationTestMarketPortfolioTailRiskAnalyzer(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"test_portfolio_{uuid.uuid4()}"
        self.confidence = round(random.uniform(0.90, 0.99), 2)
        self.horizon = random.randint(1, 10)
        self.simulation_runs = random.randint(500, 2000)

    def test_tail_risk_analyzer_integration(self):
        config = {
            "portfolio_id": self.portfolio_id,
            "confidence_level": self.confidence,
            "horizon_days": self.horizon,
            "simulation_runs": self.simulation_runs
        }

        result = market_portfolio_tail_risk_analyzer(config)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("var", result)
        self.assertIn("cvar", result)
        self.assertEqual(result.get("confidence"), self.confidence)
        self.assertEqual(result.get("horizon_days"), self.horizon)
        self.assertIn("valuation", result)
        self.assertIn("timestamp", result)

        analyzer = MarketPortfolioTailRiskAnalyzer()
        returns = [random.gauss(0.001, 0.02) for _ in range(self.simulation_runs)]

        var_dict = analyzer.compute_var(self.portfolio_id, returns, self.confidence, self.horizon)
        self.assertEqual(var_dict["portfolio_id"], self.portfolio_id)
        self.assertGreater(var_dict["var_value"], 0.0)

        cvar_val = analyzer.compute_cvar(self.portfolio_id, returns, self.confidence)
        self.assertGreater(cvar_val, 0.0)

        stress_res = analyzer.run_tail_risk_stress_test(self.portfolio_id, "market_crash", 0.15)
        self.assertIsInstance(stress_res, dict)
        self.assertEqual(stress_res.get("portfolio_id"), self.portfolio_id)

        alert_dispatched = analyzer.check_and_dispatch_risk_alert(self.portfolio_id, var_dict["var_value"] * 2, var_dict["var_value"] / 2)
        self.assertIsInstance(alert_dispatched, bool)

        persisted_state = db_storage.load_state(f"risk_report_{self.portfolio_id}")
        self.assertIsNotNone(persisted_state)
        self.assertEqual(persisted_state.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(persisted_state.get("var"), result["var"])
        self.assertEqual(persisted_state.get("cvar"), result["cvar"])

if __name__ == "__main__":
    unittest.main()