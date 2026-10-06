import unittest
import uuid
import random
from skills.market_portfolio_audit_integrity_reporter import market_portfolio_audit_integrity_reporter, MarketPortfolioAuditIntegrityReporter
from skills.db_storage import db_storage

class TestMarketPortfolioAuditIntegrityReporterIntegration(unittest.TestCase):
    def test_integration_audit_reporter_pipeline(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        audit_session_id = f"audit_{uuid.uuid4().hex[:8]}"
        discrepancy_val = round(random.uniform(0.01, 100.0), 4)

        reporter_input = {
            "portfolio_id": portfolio_id,
            "audit_session_id": audit_session_id,
            "discrepancy_detected": True,
            "report_data": {
                "discrepancy": discrepancy_val,
                "checked_items": random.randint(10, 500)
            }
        }

        result = market_portfolio_audit_integrity_reporter(reporter_input)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["audit_session_id"], audit_session_id)
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["discrepancy"], discrepancy_val)

        db_check_query = {
            "action": "get_integrity_audit",
            "portfolio_id": portfolio_id,
            "audit_session_id": audit_session_id
        }
        stored_record = db_storage(db_check_query)

        if stored_record:
            self.assertEqual(stored_record.get("portfolio_id"), portfolio_id)
            self.assertEqual(stored_record.get("audit_session_id"), audit_session_id)
            self.assertEqual(stored_record.get("discrepancy"), discrepancy_val)

if __name__ == "__main__":
    unittest.main()