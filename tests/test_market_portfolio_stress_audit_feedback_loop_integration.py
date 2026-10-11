import unittest
import uuid
import random
import os

from skills.market_portfolio_stress_audit_feedback_loop import (
    market_portfolio_stress_audit_feedback_loop
)
from skills.db_storage import db_storage
from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter
from skills.market_portfolio_strategy_optimizer import market_portfolio_strategy_optimizer

class TestMarketPortfolioStressAuditFeedbackLoopIntegration(unittest.TestCase):

    def test_feedback_loop_end_to_end_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        audit_run_id = f"audit_{random.randint(10000, 99999)}"
        initial_risk_score = round(random.uniform(10.0, 95.0), 2)

        reporter_payload = {
            "portfolio_id": portfolio_id,
            "audit_run_id": audit_run_id,
            "risk_score": initial_risk_score,
            "status": "COMPLETED"
        }

        report_result = market_portfolio_stress_reporter(reporter_payload)
        self.assertIsNotNone(report_result)

        feedback_payload = {
            "portfolio_id": portfolio_id,
            "audit_run_id": audit_run_id,
            "adjustment_factor": round(random.uniform(0.5, 1.5), 4)
        }

        loop_result = market_portfolio_stress_audit_feedback_loop(feedback_payload)

        self.assertIsInstance(loop_result, dict)
        self.assertIn("feedback_id", loop_result)
        self.assertEqual(loop_result.get("portfolio_id"), portfolio_id)
        self.assertEqual(loop_result.get("audit_run_id"), audit_run_id)

        db_record = db_storage(f"get_feedback:{loop_result['feedback_id']}")
        self.assertIsNotNone(db_record)

        optimizer_payload = {
            "portfolio_id": portfolio_id,
            "feedback_reference": loop_result["feedback_id"]
        }
        optimization_result = market_portfolio_strategy_optimizer(optimizer_payload)

        self.assertIsNotNone(optimization_result)
        self.assertIn("weights_recalculated", optimization_result)
        self.assertTrue(optimization_result["weights_recalculated"])

if __name__ == "__main__":
    unittest.main()
