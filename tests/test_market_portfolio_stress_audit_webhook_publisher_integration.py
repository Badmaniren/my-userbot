import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
from skills.db_storage import db_storage
from skills.market_portfolio_stress_audit_webhook_publisher import market_portfolio_stress_audit_webhook_publisher

class TestMarketPortfolioStressAuditWebhookPublisherIntegration(unittest.TestCase):

    def test_webhook_publisher_integration(self):
        unique_audit_id = f"audit_{uuid.uuid4()}"
        random_value = random.randint(1000, 99999)
        test_payload = {
            "audit_id": unique_audit_id,
            "metric": random_value,
            "status": "pending_stress_test"
        }

        initial_record = {
            "audit_id": unique_audit_id,
            "data": test_payload,
            "webhook_dispatched": False
        }
        db_storage.save_audit_record(initial_record)

        dummy_webhook_url = "https://httpbin.org/post"

        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"url": dummy_webhook_url, "json": test_payload}
            mock_post.return_value = mock_resp

            try:
                result = market_portfolio_stress_audit_webhook_publisher(
                    audit_id=unique_audit_id,
                    webhook_url=dummy_webhook_url
                )
            except Exception as e:
                self.fail(f"Integration execution failed with exception: {e}")

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("audit_id"), unique_audit_id)
        self.assertEqual(result.get("delivery_status"), "SUCCESS")

        updated_record = db_storage.get_audit_record(unique_audit_id)
        self.assertIsNotNone(updated_record)
        self.assertTrue(updated_record.get("webhook_dispatched"), "Flag webhook_dispatched should be set to True in db_storage")
        self.assertEqual(updated_record.get("data", {}).get("metric"), random_value)

if __name__ == "__main__":
    unittest.main()
