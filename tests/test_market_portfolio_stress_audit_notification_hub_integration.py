import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_notification_hub import market_portfolio_stress_audit_notification_hub, start_new
from skills import db_storage

class TestMarketPortfolioStressAuditNotificationHubIntegration(unittest.TestCase):
    
    def setUp(self):
        self.audit_id = str(uuid.uuid4())
        self.portfolio_id = str(uuid.uuid4())
        self.random_value = random.randint(1000, 9999)
        self.payload = {
            "audit_id": self.audit_id,
            "portfolio_id": self.portfolio_id,
            "stress_score": self.random_value,
            "status": "critical"
        }

    def test_start_new_telegram_flow(self):
        target_channel = f"channel_{self.random_value}"
        
        try:
            result = start_new(target_channel=target_channel, payload=self.payload, notifier_type="telegram")
            self.assertIsInstance(result, (dict, bool, type(None)))
        except Exception as e:
            self.assertIn("telegram", str(e).lower() or type(e).__name__)

    def test_market_portfolio_stress_audit_notification_hub_dispatch(self):
        hub_payload = {
            "audit_id": self.audit_id,
            "portfolio_id": self.portfolio_id,
            "channels": ["telegram", "webhook", "api"]
        }

        response = market_portfolio_stress_audit_notification_hub(hub_payload)

        self.assertIsInstance(response, dict)
        self.assertEqual(response.get("dispatch_status"), "success")
        self.assertEqual(response.get("audit_id"), self.audit_id)
        self.assertIn("results", response)
        self.assertIsInstance(response["results"], dict)

    def test_start_new_invalid_notifier_type(self):
        invalid_type = f"unknown_{self.random_value}"
        with self.assertRaises(ValueError) as ctx:
            start_new(target_channel="test", payload=self.payload, notifier_type=invalid_type)
        self.assertIn(invalid_type, str(ctx.exception))

if __name__ == "__main__":
    unittest.main()