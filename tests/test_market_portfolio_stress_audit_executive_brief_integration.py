import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_executive_brief import (
    MarketPortfolioStressAuditExecutiveBrief,
    market_portfolio_stress_audit_executive_brief
)
from skills.market_portfolio_stress_audit_visualizer import market_portfolio_stress_audit_visualizer
from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter
from skills.db_storage import db_storage

class TestMarketPortfolioStressAuditExecutiveBriefIntegration(unittest.TestCase):
    def test_executive_brief_class_integration(self):
        audit_id = str(uuid.uuid4())
        threshold = random.uniform(0.0, 1.0)

        brief_instance = MarketPortfolioStressAuditExecutiveBrief(
            db_storage=db_storage,
            visualizer=market_portfolio_stress_audit_visualizer,
            reporter=market_portfolio_stress_reporter
        )

        result = brief_instance.generate_brief(audit_id, threshold)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("audit_id"), audit_id)
        self.assertIn("brief_id", result)
        self.assertIn("risk_score", result)
        self.assertIn("recommendation", result)
        self.assertIsInstance(result.get("recommendations"), list)

    def test_executive_brief_functional_integration(self):
        random_portfolio_id = str(uuid.uuid4())
        random_var = random.uniform(50.0, 99.0)

        payload = {
            "portfolio_id": random_portfolio_id,
            "stress_report": {
                "var_99": random_var
            }
        }

        result = market_portfolio_stress_audit_executive_brief(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), random_portfolio_id)
        self.assertEqual(result.get("risk_score"), random_var)
        self.assertIn("brief_id", result)
        self.assertIsInstance(result.get("recommendations"), list)
        self.assertTrue(len(result.get("recommendations")) > 0)

if __name__ == "__main__":
    unittest.main()