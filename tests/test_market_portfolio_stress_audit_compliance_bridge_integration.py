import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_compliance_bridge import (
    MarketPortfolioStressAuditComplianceBridge,
    market_portfolio_stress_audit_compliance_bridge
)
from skills.market_portfolio_audit_compliance_hub import market_portfolio_audit_compliance_hub
from skills.db_storage import db_storage

class TestMarketPortfolioStressAuditComplianceBridgeIntegration(unittest.TestCase):
    def test_bridge_integration_workflow(self):
        test_portfolio_id = f"port-{uuid.uuid4()}"
        test_standard = f"STD-{random.randint(1000, 9999)}"
        test_event_payload = {
            "event_id": str(uuid.uuid4()),
            "portfolio_id": test_portfolio_id,
            "stress_score": random.uniform(0.1, 0.9)
        }

        bridge_instance = MarketPortfolioStressAuditComplianceBridge(
            db_storage=db_storage,
            market_portfolio_audit_compliance_hub=market_portfolio_audit_compliance_hub
        )

        audit_result = bridge_instance.audit_and_validate(test_portfolio_id, test_standard)
        self.assertIsInstance(audit_result, dict)

        saved_event_result = bridge_instance.process_stress_event(test_event_payload)
        self.assertIsInstance(saved_event_result, dict)

        statuses = ["COMPLIANT", "NON_COMPLIANT", "PENDING_REVIEW"]
        selected_status = random.choice(statuses)

        wrapper_input = {
            "portfolio_id": test_portfolio_id,
            "compliance_report": {
                "status": selected_status,
                "standard": test_standard
            }
        }

        wrapper_output = market_portfolio_stress_audit_compliance_bridge(wrapper_input)

        self.assertIsInstance(wrapper_output, dict)
        self.assertEqual(wrapper_output.get("portfolio_id"), test_portfolio_id)
        self.assertEqual(wrapper_output.get("audit_compliance_status"), selected_status)
        self.assertTrue(wrapper_output.get("bridge_processed"))

if __name__ == "__main__":
    unittest.main()